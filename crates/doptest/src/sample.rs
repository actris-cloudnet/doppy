use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use chrono::{Datelike, NaiveDate, Utc};
use rand::seq::SliceRandom;
use serde::Deserialize;

use toml_edit::{ArrayOfTables, DocumentMut, Item, Table, value};

use crate::api::{BASE_URL, CloudnetApi};
use crate::cluster;
use crate::features;
use crate::types::generate_id;

// ── API response types ─────────────────────────────────────────────

#[derive(Debug, Deserialize)]
pub struct InstrumentInfo {
    pub id: String,
    #[serde(rename = "type")]
    pub instrument_type: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FileRecord {
    uuid: String,
    measurement_date: String,
    size: String,
    site: SiteRef,
    product: ProductRef,
    instrument: InstrumentRef,
    download_url: String,
    filename: String,
}

#[derive(Debug, Deserialize)]
struct SiteRef {
    id: String,
}

#[derive(Debug, Deserialize)]
struct ProductRef {
    id: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct InstrumentRef {
    uuid: String,
    instrument_id: String,
}

// ── Cached record type (rkyv) ──────────────────────────────────────

#[derive(Debug, Clone, rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)]
pub struct CachedRecord {
    pub uuid: String,
    pub measurement_date: String,
    pub site_id: String,
    pub product_id: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    pub download_url: String,
    pub filename: String,
    pub size: u64,
}

impl From<FileRecord> for CachedRecord {
    fn from(r: FileRecord) -> Self {
        Self {
            uuid: r.uuid,
            measurement_date: r.measurement_date,
            site_id: r.site.id,
            product_id: r.product.id,
            instrument_id: r.instrument.instrument_id,
            instrument_uuid: r.instrument.uuid,
            download_url: r.download_url,
            filename: r.filename,
            size: r.size.parse().unwrap_or(0),
        }
    }
}

// ── Month interval generation ──────────────────────────────────────

fn monthly_intervals() -> Vec<(Option<NaiveDate>, Option<NaiveDate>)> {
    let today = Utc::now().date_naive();
    let this_month = NaiveDate::from_ymd_opt(today.year(), today.month(), 1).unwrap();
    let start = NaiveDate::from_ymd_opt(2010, 1, 1).unwrap();

    let mut intervals = Vec::new();

    intervals.push((None, Some(start)));

    let mut cursor = start;
    while cursor < this_month {
        let next = next_month(cursor);
        intervals.push((Some(cursor), Some(next)));
        cursor = next;
    }

    intervals.push((Some(this_month), None));

    intervals
}

fn next_month(date: NaiveDate) -> NaiveDate {
    if date.month() == 12 {
        NaiveDate::from_ymd_opt(date.year() + 1, 1, 1).unwrap()
    } else {
        NaiveDate::from_ymd_opt(date.year(), date.month() + 1, 1).unwrap()
    }
}

// ── Fetch + cache ──────────────────────────────────────────────────

fn cache_path() -> std::path::PathBuf {
    Path::new("tests")
        .join(".cache")
        .join("sample")
        .join("products.rkyv")
}

async fn fetch_instruments(api: &CloudnetApi) -> Result<Vec<InstrumentInfo>, String> {
    let url = format!("{BASE_URL}/instruments");
    let instruments: Vec<InstrumentInfo> = api.get_json(&url).await?;
    Ok(instruments
        .into_iter()
        .filter(|i| i.instrument_type == "doppler-lidar")
        .collect())
}

async fn fetch_files_for_interval(
    api: &CloudnetApi,
    instrument_id: &str,
    date_from: Option<NaiveDate>,
    date_to: Option<NaiveDate>,
) -> Result<Vec<FileRecord>, String> {
    let date_from_str = date_from.map(|d| d.to_string());
    let date_to_str = date_to.map(|d| d.to_string());

    let mut params: Vec<(&str, &str)> = vec![("instrument", instrument_id)];
    if let Some(from) = &date_from_str {
        params.push(("dateFrom", from));
    }
    if let Some(to) = &date_to_str {
        params.push(("dateTo", to));
    }

    let url = reqwest::Url::parse_with_params(&format!("{BASE_URL}/files"), &params)
        .map_err(|e| format!("invalid URL params: {e}"))?;

    api.get_json(url.as_str()).await
}

async fn load_or_fetch_cache(force: bool) -> Result<Vec<CachedRecord>, String> {
    let path = cache_path();

    if !force && path.exists() {
        let bytes = fs::read(&path).map_err(|e| format!("failed to read cache: {e}"))?;
        let records: Vec<CachedRecord> =
            rkyv::from_bytes::<Vec<CachedRecord>, rkyv::rancor::Error>(&bytes)
                .map_err(|e| format!("failed to deserialize cache: {e}"))?;
        return Ok(records);
    }

    let api = CloudnetApi::new()?;
    let instruments = fetch_instruments(&api).await?;

    eprintln!(
        "Found {} doppler-lidar instrument types: {}",
        instruments.len(),
        instruments
            .iter()
            .map(|i| i.id.as_str())
            .collect::<Vec<_>>()
            .join(", ")
    );

    let intervals = monthly_intervals();
    let total_intervals = intervals.len();
    let mut all_records: Vec<CachedRecord> = Vec::new();

    for (instr_idx, instrument) in instruments.iter().enumerate() {
        eprintln!(
            "\n[{}/{}] Fetching {}...",
            instr_idx + 1,
            instruments.len(),
            instrument.id
        );

        let mut instrument_count = 0usize;
        for (i, (from, to)) in intervals.iter().enumerate() {
            eprint!("\r  [{}/{}] ", i + 1, total_intervals,);
            match fetch_files_for_interval(&api, &instrument.id, *from, *to).await {
                Ok(records) => {
                    let count = records.len();
                    instrument_count += count;
                    all_records.extend(records.into_iter().map(CachedRecord::from));
                }
                Err(e) => {
                    eprintln!("error: {e}");
                }
            }
        }
        eprintln!("\r  -> {instrument_count} files");
    }

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("failed to create cache dir: {e}"))?;
    }
    let bytes = rkyv::to_bytes::<rkyv::rancor::Error>(&all_records)
        .map_err(|e| format!("failed to serialize: {e}"))?;
    fs::write(&path, &bytes).map_err(|e| format!("failed to write cache: {e}"))?;

    eprintln!(
        "\nDone: {} total records cached to {}",
        all_records.len(),
        path.display()
    );
    Ok(all_records)
}

pub async fn cmd_sample_fetch(force: bool) -> Result<(), String> {
    let records = load_or_fetch_cache(force).await?;
    eprintln!("{} records in cache.", records.len());
    Ok(())
}

#[allow(clippy::too_many_lines)]
pub async fn cmd_sample_stare(
    n: usize,
    force: bool,
    per_cluster: usize,
    add: bool,
) -> Result<(), String> {
    let records = load_or_fetch_cache(force).await?;

    let stare_records: Vec<&CachedRecord> = records
        .iter()
        .filter(|r| r.product_id == "doppler-lidar")
        .collect();

    eprintln!(
        "{} stare records out of {} total.",
        stare_records.len(),
        records.len()
    );

    let mut groups: BTreeMap<(&str, &str), Vec<&CachedRecord>> = BTreeMap::new();
    for r in &stare_records {
        groups
            .entry((&r.site_id, &r.instrument_uuid))
            .or_default()
            .push(r);
    }

    eprintln!("{} distinct (site, instrument) pairs.", groups.len());

    let sampled_records: Vec<CachedRecord> = {
        let mut rng = rand::rng();
        let mut sampled = Vec::new();
        for ((site, instrument_uuid), mut files) in groups {
            let total = files.len();
            let take = n.min(total);
            files.shuffle(&mut rng);

            let instrument_id = &files[0].instrument_id;
            eprintln!("{site:>20} {instrument_id:<24} {instrument_uuid}  ({take}/{total})");

            for r in &files[..take] {
                sampled.push((*r).clone());
            }
        }
        sampled
    };

    let total = sampled_records.len();
    eprintln!("\nDownloading {total} files...");

    let api = CloudnetApi::new()?;
    let tmp_dir = std::env::temp_dir();

    let mut results: Vec<features::SampleResult> = Vec::new();
    let mut errors = 0u32;
    for (done, rec) in sampled_records.into_iter().enumerate() {
        let outcome: Result<features::SampleResult, String> = async {
            let bytes = api.download_bytes(&rec.download_url).await?;
            let path = tmp_dir.join(&rec.uuid);
            fs::write(&path, &bytes).map_err(|e| format!("write {}: {e}", path.display()))?;
            let r = features::extract_features(&path, &rec);
            let _ = fs::remove_file(&path);
            r
        }
        .await;
        eprint!("\r  [{}/{total}]", done + 1);
        match outcome {
            Ok(result) => results.push(result),
            Err(e) => {
                errors += 1;
                eprintln!("  \x1b[31mERR\x1b[0m {e}");
            }
        }
    }
    eprintln!();

    eprintln!(
        "Done: {} features extracted, {errors} errors.",
        results.len()
    );

    let n_samples = results.len();
    if n_samples < 2 {
        eprintln!("Too few samples for clustering ({n_samples}), outputting all.");
        let json =
            serde_json::to_string_pretty(&results).map_err(|e| format!("serialize error: {e}"))?;
        println!("{json}");
        return Ok(());
    }

    let feature_vecs: Vec<Vec<f64>> = results.iter().map(|r| r.features.to_vec()).collect();
    let min_k = 5.min(n_samples - 1).max(2);
    let max_k = 25.min(n_samples - 1).max(min_k);

    eprintln!("Clustering {n_samples} samples, sweeping k={min_k}..={max_k}...");

    let clustering = cluster::cluster_and_select(&feature_vecs, min_k..=max_k, per_cluster)?;

    println!(
        "Selected k={}, inertia={:.1}, {} files selected.\n",
        clustering.k,
        clustering.inertia,
        clustering.selected.len(),
    );
    println!(
        "  {:>7}  {:<20} {:<12} instrument_uuid",
        "cluster", "site", "date"
    );
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;
        println!(
            "  {:>7}  {:<20} {:<12} {}",
            a.cluster, m.site, m.date, m.instrument_uuid
        );
    }

    println!("\nCluster sizes:");
    for (i, &size) in clustering.cluster_sizes.iter().enumerate() {
        println!("  {i:>3}: {size}");
    }

    let n_pairs = 5.min(clustering.centroid_distances.len());
    println!("\nClosest centroid pairs:");
    for &(a, b, d) in &clustering.centroid_distances[..n_pairs] {
        println!("  ({a}, {b})  d={d:.2}");
    }

    println!("\nFarthest centroid pairs:");
    for &(a, b, d) in clustering.centroid_distances.iter().rev().take(n_pairs) {
        println!("  ({a}, {b})  d={d:.2}");
    }

    if add {
        add_samples_to_config(&results, &clustering)?;
    }

    Ok(())
}

#[allow(clippy::too_many_lines)]
pub async fn cmd_sample_wind(
    n: usize,
    force: bool,
    per_cluster: usize,
    add: bool,
) -> Result<(), String> {
    let records = load_or_fetch_cache(force).await?;

    let wind_records: Vec<&CachedRecord> = records
        .iter()
        .filter(|r| r.product_id == "doppler-lidar-wind")
        .collect();

    eprintln!(
        "{} wind records out of {} total.",
        wind_records.len(),
        records.len()
    );

    let mut groups: BTreeMap<(&str, &str), Vec<&CachedRecord>> = BTreeMap::new();
    for r in &wind_records {
        groups
            .entry((&r.site_id, &r.instrument_uuid))
            .or_default()
            .push(r);
    }

    eprintln!("{} distinct (site, instrument) pairs.", groups.len());

    let sampled_records: Vec<CachedRecord> = {
        let mut rng = rand::rng();
        let mut sampled = Vec::new();
        for ((site, instrument_uuid), mut files) in groups {
            let total = files.len();
            let take = n.min(total);
            files.shuffle(&mut rng);

            let instrument_id = &files[0].instrument_id;
            eprintln!("{site:>20} {instrument_id:<24} {instrument_uuid}  ({take}/{total})");

            for r in &files[..take] {
                sampled.push((*r).clone());
            }
        }
        sampled
    };

    let total = sampled_records.len();
    eprintln!("\nDownloading {total} files...");

    let api = CloudnetApi::new()?;
    let tmp_dir = std::env::temp_dir();

    let mut results: Vec<features::WindSampleResult> = Vec::new();
    let mut errors = 0u32;
    for (done, rec) in sampled_records.into_iter().enumerate() {
        let outcome: Result<features::WindSampleResult, String> = async {
            let bytes = api.download_bytes(&rec.download_url).await?;
            let path = tmp_dir.join(&rec.uuid);
            fs::write(&path, &bytes).map_err(|e| format!("write {}: {e}", path.display()))?;
            let r = features::extract_wind_features(&path, &rec);
            let _ = fs::remove_file(&path);
            r
        }
        .await;
        eprint!("\r  [{}/{total}]", done + 1);
        match outcome {
            Ok(result) => results.push(result),
            Err(e) => {
                errors += 1;
                eprintln!("  \x1b[31mERR\x1b[0m {e}");
            }
        }
    }
    eprintln!();

    eprintln!(
        "Done: {} features extracted, {errors} errors.",
        results.len()
    );

    let n_samples = results.len();
    if n_samples < 2 {
        eprintln!("Too few samples for clustering ({n_samples}), outputting all.");
        let json =
            serde_json::to_string_pretty(&results).map_err(|e| format!("serialize error: {e}"))?;
        println!("{json}");
        return Ok(());
    }

    let feature_vecs: Vec<Vec<f64>> = results.iter().map(|r| r.features.to_vec()).collect();
    let min_k = 5.min(n_samples - 1).max(2);
    let max_k = 25.min(n_samples - 1).max(min_k);

    eprintln!("Clustering {n_samples} samples, sweeping k={min_k}..={max_k}...");

    let clustering = cluster::cluster_and_select(&feature_vecs, min_k..=max_k, per_cluster)?;

    println!(
        "Selected k={}, inertia={:.1}, {} files selected.\n",
        clustering.k,
        clustering.inertia,
        clustering.selected.len(),
    );
    println!(
        "  {:>7}  {:<20} {:<12} instrument_uuid",
        "cluster", "site", "date"
    );
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;
        println!(
            "  {:>7}  {:<20} {:<12} {}",
            a.cluster, m.site, m.date, m.instrument_uuid
        );
    }

    println!("\nCluster sizes:");
    for (i, &size) in clustering.cluster_sizes.iter().enumerate() {
        println!("  {i:>3}: {size}");
    }

    let n_pairs = 5.min(clustering.centroid_distances.len());
    println!("\nClosest centroid pairs:");
    for &(a, b, d) in &clustering.centroid_distances[..n_pairs] {
        println!("  ({a}, {b})  d={d:.2}");
    }

    println!("\nFarthest centroid pairs:");
    for &(a, b, d) in clustering.centroid_distances.iter().rev().take(n_pairs) {
        println!("  ({a}, {b})  d={d:.2}");
    }

    if add {
        add_wind_samples_to_config(&results, &clustering)?;
    }

    Ok(())
}

#[allow(clippy::too_many_lines)]
pub async fn cmd_sample_turbulence(
    n: usize,
    force: bool,
    per_cluster: usize,
    add: bool,
) -> Result<(), String> {
    let records = load_or_fetch_cache(force).await?;

    let turb_records: Vec<&CachedRecord> = records
        .iter()
        .filter(|r| r.product_id == "epsilon-lidar")
        .collect();

    eprintln!(
        "{} turbulence records out of {} total.",
        turb_records.len(),
        records.len()
    );

    let mut groups: BTreeMap<(&str, &str), Vec<&CachedRecord>> = BTreeMap::new();
    for r in &turb_records {
        groups
            .entry((&r.site_id, &r.instrument_uuid))
            .or_default()
            .push(r);
    }

    eprintln!("{} distinct (site, instrument) pairs.", groups.len());

    let sampled_records: Vec<CachedRecord> = {
        let mut rng = rand::rng();
        let mut sampled = Vec::new();
        for ((site, instrument_uuid), mut files) in groups {
            let total = files.len();
            let take = n.min(total);
            files.shuffle(&mut rng);

            let instrument_id = &files[0].instrument_id;
            eprintln!("{site:>20} {instrument_id:<24} {instrument_uuid}  ({take}/{total})");

            for r in &files[..take] {
                sampled.push((*r).clone());
            }
        }
        sampled
    };

    let total = sampled_records.len();
    eprintln!("\nDownloading {total} files...");

    let api = CloudnetApi::new()?;
    let tmp_dir = std::env::temp_dir();

    let mut results: Vec<features::TurbulenceSampleResult> = Vec::new();
    let mut errors = 0u32;
    for (done, rec) in sampled_records.into_iter().enumerate() {
        let outcome: Result<features::TurbulenceSampleResult, String> = async {
            let bytes = api.download_bytes(&rec.download_url).await?;
            let path = tmp_dir.join(&rec.uuid);
            fs::write(&path, &bytes).map_err(|e| format!("write {}: {e}", path.display()))?;
            let r = features::extract_turbulence_features(&path, &rec);
            let _ = fs::remove_file(&path);
            r
        }
        .await;
        eprint!("\r  [{}/{total}]", done + 1);
        match outcome {
            Ok(result) => results.push(result),
            Err(e) => {
                errors += 1;
                eprintln!("  \x1b[31mERR\x1b[0m {e}");
            }
        }
    }
    eprintln!();

    eprintln!(
        "Done: {} features extracted, {errors} errors.",
        results.len()
    );

    let n_samples = results.len();
    if n_samples < 2 {
        eprintln!("Too few samples for clustering ({n_samples}), outputting all.");
        let json =
            serde_json::to_string_pretty(&results).map_err(|e| format!("serialize error: {e}"))?;
        println!("{json}");
        return Ok(());
    }

    let feature_vecs: Vec<Vec<f64>> = results.iter().map(|r| r.features.to_vec()).collect();
    let min_k = 5.min(n_samples - 1).max(2);
    let max_k = 25.min(n_samples - 1).max(min_k);

    eprintln!("Clustering {n_samples} samples, sweeping k={min_k}..={max_k}...");

    let clustering = cluster::cluster_and_select(&feature_vecs, min_k..=max_k, per_cluster)?;

    println!(
        "Selected k={}, inertia={:.1}, {} files selected.\n",
        clustering.k,
        clustering.inertia,
        clustering.selected.len(),
    );
    println!(
        "  {:>7}  {:<20} {:<12} instrument_uuid",
        "cluster", "site", "date"
    );
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;
        println!(
            "  {:>7}  {:<20} {:<12} {}",
            a.cluster, m.site, m.date, m.instrument_uuid
        );
    }

    println!("\nCluster sizes:");
    for (i, &size) in clustering.cluster_sizes.iter().enumerate() {
        println!("  {i:>3}: {size}");
    }

    let n_pairs = 5.min(clustering.centroid_distances.len());
    println!("\nClosest centroid pairs:");
    for &(a, b, d) in &clustering.centroid_distances[..n_pairs] {
        println!("  ({a}, {b})  d={d:.2}");
    }

    println!("\nFarthest centroid pairs:");
    for &(a, b, d) in clustering.centroid_distances.iter().rev().take(n_pairs) {
        println!("  ({a}, {b})  d={d:.2}");
    }

    if add {
        add_turbulence_samples_to_config(&results, &clustering)?;
    }

    Ok(())
}

fn add_turbulence_samples_to_config(
    results: &[features::TurbulenceSampleResult],
    clustering: &cluster::ClusteringResult,
) -> Result<(), String> {
    let path = Path::new("tests").join("tests.toml");
    let text = fs::read_to_string(&path).unwrap_or_default();
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

    if doc.get("turbulence").is_none() {
        doc.insert("turbulence", Item::ArrayOfTables(ArrayOfTables::new()));
    }
    let arr = doc["turbulence"]
        .as_array_of_tables_mut()
        .ok_or_else(|| "'turbulence' is not an array of tables in tests.toml".to_string())?;

    let mut added = 0u32;
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;

        let id = generate_id();
        let mut t = Table::new();
        t.insert("id", value(&id));
        t.insert("site", value(&m.site));
        t.insert("date", value(&m.date));
        t.insert("instrument_id", value(&m.instrument_id));
        t.insert("instrument_uuid", value(&m.instrument_uuid));
        t.insert("description", value("added by doptest sample"));
        arr.push(t);
        added += 1;

        println!("Added [{id}] turbulence {:<20} {}", m.site, m.date);
    }

    fs::write(&path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

    println!("\n{added} test(s) added to {}", path.display());
    Ok(())
}

fn add_wind_samples_to_config(
    results: &[features::WindSampleResult],
    clustering: &cluster::ClusteringResult,
) -> Result<(), String> {
    let path = Path::new("tests").join("tests.toml");
    let text = fs::read_to_string(&path).unwrap_or_default();
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

    if doc.get("wind").is_none() {
        doc.insert("wind", Item::ArrayOfTables(ArrayOfTables::new()));
    }
    let arr = doc["wind"]
        .as_array_of_tables_mut()
        .ok_or_else(|| "'wind' is not an array of tables in tests.toml".to_string())?;

    let mut added = 0u32;
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;

        let id = generate_id();
        let mut t = Table::new();
        t.insert("id", value(&id));
        t.insert("site", value(&m.site));
        t.insert("date", value(&m.date));
        t.insert("instrument_id", value(&m.instrument_id));
        t.insert("instrument_uuid", value(&m.instrument_uuid));
        t.insert("description", value("added by doptest sample"));
        arr.push(t);
        added += 1;

        println!("Added [{id}] wind {:<20} {}", m.site, m.date);
    }

    fs::write(&path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

    println!("\n{added} test(s) added to {}", path.display());
    Ok(())
}

fn add_samples_to_config(
    results: &[features::SampleResult],
    clustering: &cluster::ClusteringResult,
) -> Result<(), String> {
    let path = Path::new("tests").join("tests.toml");
    let text = fs::read_to_string(&path).unwrap_or_default();
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

    if doc.get("stare").is_none() {
        doc.insert("stare", Item::ArrayOfTables(ArrayOfTables::new()));
    }
    let arr = doc["stare"]
        .as_array_of_tables_mut()
        .ok_or_else(|| "'stare' is not an array of tables in tests.toml".to_string())?;

    let mut added = 0u32;
    for &idx in &clustering.selected {
        let a = &clustering.assignments[idx];
        let m = &results[a.index].metadata;

        let id = generate_id();
        let mut t = Table::new();
        t.insert("id", value(&id));
        t.insert("site", value(&m.site));
        t.insert("date", value(&m.date));
        t.insert("instrument_id", value(&m.instrument_id));
        t.insert("instrument_uuid", value(&m.instrument_uuid));
        t.insert("description", value("added by doptest sample"));
        arr.push(t);
        added += 1;

        println!("Added [{id}] stare {:<20} {}", m.site, m.date);
    }

    fs::write(&path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

    println!("\n{added} test(s) added to {}", path.display());
    Ok(())
}

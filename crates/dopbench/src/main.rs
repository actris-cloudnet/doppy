use std::fs;
use std::io::Read as _;
use std::path::{Path, PathBuf};
use std::time::Duration;

use clap::{Parser, Subcommand};
use rand::distr::{Alphanumeric, SampleString};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use toml_edit::{ArrayOfTables, DocumentMut, Item, Table, value};

// ── Constants ───────────────────────────────────────────────────────

const BASE_URL: &str = "https://cloudnet.fmi.fi/api";
const TIMEOUT_SECS: u64 = 1800;
const MAX_RETRIES: u32 = 10;
const BACKOFF_FACTOR: f64 = 0.2;

const PERCENTILES: &[(&str, u8)] = &[
    ("p25", 25),
    ("p50", 50),
    ("p75", 75),
    ("p90", 90),
    ("p99", 99),
    ("p100", 100),
];

// ── CLI ─────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(name = "dopbench", about = "Doppy benchmark tool")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Add a benchmark entry to bench.toml
    Add {
        #[command(subcommand)]
        product: AddProduct,
    },
    /// List benchmark entries from bench.toml
    List {
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// List only the entry with this id
        id: Option<String>,
    },
    /// Remove a benchmark entry by id
    Remove {
        /// The entry id to remove
        id: String,
    },
    /// Select benchmark files from Cloudnet
    Sample {
        #[command(subcommand)]
        product: SampleProduct,
    },
    /// Download files and generate bench.lock
    Lock {
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Lock only the entry with this id
        id: Option<String>,
    },
    /// Run benchmarks
    Run {
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Run only the entry with this id
        id: Option<String>,
        /// Save results to bench.lock
        #[arg(long)]
        save: bool,
    },
    /// Profile stare processing for a bench entry
    Profile {
        /// The entry id to profile
        id: String,
        /// Profiler to use
        #[arg(long, value_enum, default_value_t = Profiler::PySpy)]
        profiler: Profiler,
        /// Output format (py-spy only)
        #[arg(long, short, value_enum, default_value_t = ProfileFormat::Flamegraph)]
        format: ProfileFormat,
        /// Output file path (auto-generated if omitted)
        #[arg(long, short)]
        output: Option<String>,
        /// Include native (Rust/C) frames (py-spy only)
        #[arg(long)]
        native: bool,
        /// Open the output file after profiling
        #[arg(long)]
        open: bool,
    },
}

#[derive(Subcommand)]
enum AddProduct {
    /// Add a stare benchmark entry
    Stare {
        site: String,
        date: String,
        instrument_uuid: Option<String>,
        #[arg(long)]
        percentile: Option<String>,
        #[arg(long)]
        description: Option<String>,
    },
}

#[derive(Clone, clap::ValueEnum)]
enum Profiler {
    PySpy,
    Cprofile,
}

#[derive(Clone, clap::ValueEnum)]
enum ProfileFormat {
    Flamegraph,
    Raw,
    Speedscope,
    Chrometrace,
}

impl ProfileFormat {
    const fn py_spy_flag(&self) -> &str {
        match self {
            Self::Flamegraph => "flamegraph",
            Self::Raw => "raw",
            Self::Speedscope => "speedscope",
            Self::Chrometrace => "chrometrace",
        }
    }

    const fn extension(&self) -> &str {
        match self {
            Self::Flamegraph => "svg",
            Self::Raw => "txt",
            Self::Speedscope => "speedscope.json",
            Self::Chrometrace => "json",
        }
    }
}

#[derive(Subcommand)]
enum SampleProduct {
    /// Sample stare (doppler-lidar) files by size percentile
    Stare {
        /// Add selected samples to bench.toml
        #[arg(long)]
        add: bool,
    },
}

// ── API response types ──────────────────────────────────────────────

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FileRecord {
    measurement_date: String,
    size: String,
    site: SiteRef,
    instrument: InstrumentRef,
}

#[derive(Debug, Deserialize)]
struct SiteRef {
    id: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct InstrumentRef {
    uuid: String,
    instrument_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RawRecord {
    filename: String,
    uuid: String,
    download_url: String,
    instrument: Instrument,
    #[serde(default)]
    tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Instrument {
    uuid: String,
    instrument_id: String,
}

// ── TOML types ──────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct BenchConfig {
    #[serde(default)]
    stare: Vec<BenchEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
struct BenchEntry {
    id: String,
    site: String,
    date: String,
    instrument_id: String,
    instrument_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    percentile: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    description: Option<String>,
}

impl std::fmt::Display for BenchEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "[\x1b[36m{}\x1b[0m] stare {} {} ({})",
            self.id, self.site, self.date, self.instrument_id,
        )?;
        if let Some(p) = &self.percentile {
            write!(f, " {p}")?;
        }
        Ok(())
    }
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct LockMeta {
    locked_at: String,
    doppy_version: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct RunMeta {
    date: String,
    doppy_version: String,
    os: String,
    arch: String,
    os_version: String,
    cpu: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct BenchLock {
    #[serde(default)]
    meta: LockMeta,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    run: Option<RunMeta>,
    #[serde(default)]
    stare: Vec<LockEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
struct LockEntry {
    id: String,
    site: String,
    date: String,
    instrument_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    elapsed_secs: Option<f64>,
    input: LockInput,
}

#[derive(Debug, Serialize, Deserialize)]
struct LockInput {
    files: Vec<InputFile>,
}

#[derive(Debug, Serialize, Deserialize)]
struct InputFile {
    filename: String,
    uuid: String,
    sha256: String,
}

// ── HTTP client ─────────────────────────────────────────────────────

struct CloudnetApi {
    client: Client,
}

impl CloudnetApi {
    fn new() -> Result<Self, String> {
        let client = Client::builder()
            .timeout(Duration::from_secs(TIMEOUT_SECS))
            .build()
            .map_err(|e| format!("failed to create HTTP client: {e}"))?;
        Ok(Self { client })
    }

    async fn get_with_retry(&self, url: &str) -> Result<reqwest::Response, String> {
        let mut last_err = String::new();
        for attempt in 0..=MAX_RETRIES {
            if attempt > 0 {
                let delay = BACKOFF_FACTOR * f64::from(attempt);
                tokio::time::sleep(Duration::from_secs_f64(delay)).await;
            }
            match self.client.get(url).send().await {
                Ok(resp) if resp.status().is_success() => return Ok(resp),
                Ok(resp) if resp.status().is_server_error() => {
                    last_err = format!("server error: {}", resp.status());
                }
                Ok(resp) => {
                    return Err(format!("API request failed: {}", resp.status()));
                }
                Err(e) => {
                    last_err = format!("request error: {e}");
                }
            }
        }
        Err(format!("failed after {MAX_RETRIES} retries: {last_err}"))
    }

    async fn get_json<T: serde::de::DeserializeOwned>(&self, url: &str) -> Result<T, String> {
        let resp = self.get_with_retry(url).await?;
        resp.json()
            .await
            .map_err(|e| format!("failed to parse response: {e}"))
    }

    async fn get_product_files(&self, product: &str) -> Result<Vec<FileRecord>, String> {
        let url =
            reqwest::Url::parse_with_params(&format!("{BASE_URL}/files"), &[("product", product)])
                .map_err(|e| format!("invalid URL params: {e}"))?;
        self.get_json(url.as_str()).await
    }

    async fn get_raw_files(&self, site: &str, date: &str) -> Result<Vec<RawRecord>, String> {
        let url = reqwest::Url::parse_with_params(
            &format!("{BASE_URL}/raw-files"),
            &[("site", site), ("date", date)],
        )
        .map_err(|e| format!("invalid URL params: {e}"))?;
        self.get_json(url.as_str()).await
    }

    async fn get_raw_files_for_instrument(
        &self,
        site: &str,
        date: &str,
        instrument_uuid: &str,
    ) -> Result<Vec<RawRecord>, String> {
        let records = self.get_raw_files(site, date).await?;
        Ok(records
            .into_iter()
            .filter(|r| r.instrument.uuid == instrument_uuid)
            .collect())
    }

    async fn download_bytes(&self, url: &str) -> Result<Vec<u8>, String> {
        let resp = self.get_with_retry(url).await?;
        let bytes = resp
            .bytes()
            .await
            .map_err(|e| format!("failed to read response body: {e}"))?;
        Ok(bytes.into())
    }
}

// ── Paths & cache ───────────────────────────────────────────────────

fn tests_dir() -> PathBuf {
    PathBuf::from("tests")
}

fn bench_config_path() -> PathBuf {
    tests_dir().join("bench.toml")
}

fn bench_lock_path() -> PathBuf {
    tests_dir().join("bench.lock")
}

fn cache_dir() -> PathBuf {
    tests_dir().join(".cache").join("bench")
}

fn cache_file_path(uuid: &str) -> PathBuf {
    cache_dir().join("files").join(uuid)
}

fn cache_records_path(id: &str) -> PathBuf {
    cache_dir().join("records").join(format!("{id}.json"))
}

fn profiles_dir() -> PathBuf {
    cache_dir().join("profiles")
}

fn has_cached_file(uuid: &str) -> bool {
    cache_file_path(uuid).exists()
}

fn store_cached_file(uuid: &str, content: &[u8]) -> Result<(), String> {
    let path = cache_file_path(uuid);
    fs::create_dir_all(path.parent().unwrap())
        .map_err(|e| format!("failed to create cache dir: {e}"))?;
    fs::write(&path, content).map_err(|e| format!("failed to write cache file: {e}"))
}

fn store_cached_records(id: &str, records: &[RawRecord]) -> Result<(), String> {
    let path = cache_records_path(id);
    fs::create_dir_all(path.parent().unwrap())
        .map_err(|e| format!("failed to create records dir: {e}"))?;
    let json =
        serde_json::to_string_pretty(records).map_err(|e| format!("serialize error: {e}"))?;
    fs::write(&path, json).map_err(|e| format!("failed to write records: {e}"))
}

fn load_cached_records(id: &str) -> Option<Vec<RawRecord>> {
    let path = cache_records_path(id);
    let text = fs::read_to_string(&path).ok()?;
    serde_json::from_str(&text).ok()
}

// ── Helpers ─────────────────────────────────────────────────────────

fn python_path() -> String {
    if let Ok(venv) = std::env::var("VIRTUAL_ENV") {
        let bin = PathBuf::from(venv).join("bin").join("python");
        if bin.exists() {
            return bin.to_string_lossy().to_string();
        }
    }
    "python".to_string()
}

fn generate_id() -> String {
    Alphanumeric
        .sample_string(&mut rand::rng(), 6)
        .to_ascii_lowercase()
}

fn decompress_if_gz(filename: &str, data: Vec<u8>) -> Result<Vec<u8>, String> {
    if Path::new(filename)
        .extension()
        .is_some_and(|ext| ext.eq_ignore_ascii_case("gz"))
    {
        let mut decoder = flate2::read::GzDecoder::new(data.as_slice());
        let mut decompressed = Vec::new();
        decoder
            .read_to_end(&mut decompressed)
            .map_err(|e| format!("gzip decompression failed for {filename}: {e}"))?;
        Ok(decompressed)
    } else {
        Ok(data)
    }
}

fn file_sha256(path: &Path) -> Result<String, String> {
    let content = fs::read(path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let hash = Sha256::digest(&content);
    Ok(format!("{hash:x}"))
}

fn format_size(bytes: u64) -> String {
    #[allow(clippy::cast_precision_loss)]
    let b = bytes as f64;
    if bytes >= 1_073_741_824 {
        format!("{:.1} GiB", b / 1_073_741_824.0)
    } else if bytes >= 1_048_576 {
        format!("{:.1} MiB", b / 1_048_576.0)
    } else if bytes >= 1024 {
        format!("{:.1} KiB", b / 1024.0)
    } else {
        format!("{bytes} B")
    }
}

fn build_local_records(records: &[RawRecord]) -> Result<Vec<serde_json::Value>, String> {
    let cache = cache_dir();
    let abs_root = if cache.is_absolute() {
        cache
    } else {
        std::env::current_dir()
            .map_err(|e| format!("failed to get cwd: {e}"))?
            .join(cache)
            .canonicalize()
            .map_err(|e| format!("failed to canonicalize cache path: {e}"))?
    };
    records
        .iter()
        .map(|r| {
            let path = abs_root.join("files").join(&r.uuid);
            let path_str = path
                .to_str()
                .ok_or_else(|| "non-UTF-8 cache path".to_string())?;
            Ok(serde_json::json!({
                "filename": r.filename,
                "uuid": r.uuid,
                "path": path_str,
                "instrument_id": r.instrument.instrument_id,
                "tags": r.tags,
            }))
        })
        .collect()
}

fn read_config() -> Result<BenchConfig, String> {
    let path = bench_config_path();
    let text = fs::read_to_string(&path).unwrap_or_default();
    toml::from_str(&text).map_err(|e| format!("failed to parse {}: {e}", path.display()))
}

fn filter_entries<'a>(
    entries: &'a [BenchEntry],
    site_filter: Option<&str>,
    id_filter: Option<&str>,
) -> Vec<&'a BenchEntry> {
    entries
        .iter()
        .filter(|e| {
            site_filter.is_none_or(|s| e.site == s) && id_filter.is_none_or(|id| e.id == id)
        })
        .collect()
}

// ── Instrument resolution ───────────────────────────────────────────

async fn resolve_instrument(
    api: &CloudnetApi,
    site: &str,
    date: &str,
) -> Result<(String, String), String> {
    let records = api.get_raw_files(site, date).await?;

    let mut seen = std::collections::HashMap::new();
    for r in &records {
        seen.entry(r.instrument.uuid.clone())
            .or_insert_with(|| r.instrument.instrument_id.clone());
    }

    match seen.len() {
        0 => Err(format!("no instruments found at site '{site}' on {date}")),
        1 => {
            let (uuid, instrument_id) = seen.into_iter().next().unwrap();
            eprintln!("Resolved instrument: {uuid} ({instrument_id})");
            Ok((instrument_id, uuid))
        }
        _ => {
            eprintln!("Multiple instruments found at site '{site}' on {date}:");
            for (uuid, instrument_id) in &seen {
                eprintln!("  {uuid}  ({instrument_id})");
            }
            Err(
                "ambiguous: multiple instruments found, specify the instrument UUID explicitly"
                    .into(),
            )
        }
    }
}

async fn resolve_instrument_id(
    api: &CloudnetApi,
    site: &str,
    date: &str,
    instrument_uuid: &str,
) -> Result<String, String> {
    let records = api
        .get_raw_files_for_instrument(site, date, instrument_uuid)
        .await?;
    records
        .first()
        .map(|r| r.instrument.instrument_id.clone())
        .ok_or_else(|| {
            format!("no records found for instrument {instrument_uuid} at {site} on {date}")
        })
}

// ── Commands ────────────────────────────────────────────────────────

async fn cmd_add(api: &CloudnetApi, product: AddProduct) -> Result<(), String> {
    let path = bench_config_path();
    let text = fs::read_to_string(&path).unwrap_or_default();
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

    let id = generate_id();

    let (table_name, table) = match product {
        AddProduct::Stare {
            site,
            date,
            instrument_uuid,
            percentile,
            description,
        } => {
            let (instrument_id, instrument_uuid) = if let Some(uuid) = instrument_uuid {
                let id = resolve_instrument_id(api, &site, &date, &uuid).await?;
                (id, uuid)
            } else {
                resolve_instrument(api, &site, &date).await?
            };
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            t.insert("instrument_id", value(&instrument_id));
            t.insert("instrument_uuid", value(&instrument_uuid));
            if let Some(p) = &percentile {
                t.insert("percentile", value(p));
            }
            if let Some(d) = &description {
                t.insert("description", value(d));
            }
            ("stare", t)
        }
    };

    if doc.get(table_name).is_none() {
        doc.insert(table_name, Item::ArrayOfTables(ArrayOfTables::new()));
    }
    let arr = doc[table_name]
        .as_array_of_tables_mut()
        .ok_or_else(|| format!("'{table_name}' is not an array of tables in bench.toml"))?;
    arr.push(table);

    fs::write(&path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

    println!("Added [{id}] to [[{table_name}]] in {}", path.display());
    Ok(())
}

fn cmd_list(site_filter: Option<&str>, id_filter: Option<&str>) -> Result<(), String> {
    let config = read_config()?;
    let filtered = filter_entries(&config.stare, site_filter, id_filter);

    if filtered.is_empty() {
        println!("No entries match the given filters.");
        return Ok(());
    }

    println!("{} entry(ies):\n", filtered.len());
    for entry in &filtered {
        println!("  {entry}");
    }
    Ok(())
}

fn cmd_remove(id: &str) -> Result<(), String> {
    let config = read_config()?;
    let entry = config
        .stare
        .iter()
        .find(|e| e.id == id)
        .ok_or_else(|| format!("no entry found with id '{id}'"))?;

    println!("  {entry}");
    print!("Remove? [y/N] ");
    std::io::Write::flush(&mut std::io::stdout())
        .map_err(|e| format!("failed to flush stdout: {e}"))?;

    let mut answer = String::new();
    std::io::stdin()
        .read_line(&mut answer)
        .map_err(|e| format!("failed to read input: {e}"))?;
    if !matches!(answer.trim(), "y" | "Y") {
        println!("Aborted.");
        return Ok(());
    }

    let config_path = bench_config_path();
    let text = fs::read_to_string(&config_path)
        .map_err(|e| format!("failed to read {}: {e}", config_path.display()))?;
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", config_path.display()))?;

    remove_from_toml_array(&mut doc, "stare", id);
    fs::write(&config_path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", config_path.display()))?;

    let lock_path = bench_lock_path();
    if lock_path.exists() {
        let lock_text = fs::read_to_string(&lock_path)
            .map_err(|e| format!("failed to read {}: {e}", lock_path.display()))?;
        let mut lock_doc: DocumentMut = lock_text
            .parse()
            .map_err(|e| format!("failed to parse {}: {e}", lock_path.display()))?;
        remove_from_toml_array(&mut lock_doc, "stare", id);
        fs::write(&lock_path, lock_doc.to_string())
            .map_err(|e| format!("failed to write {}: {e}", lock_path.display()))?;
    }

    println!("Removed [{id}]");
    Ok(())
}

fn remove_from_toml_array(doc: &mut DocumentMut, table_name: &str, id: &str) {
    if let Some(arr) = doc
        .get_mut(table_name)
        .and_then(|v| v.as_array_of_tables_mut())
    {
        let pos = (0..arr.len()).find(|&i| {
            arr.get(i)
                .and_then(|t| t.get("id"))
                .and_then(|v| v.as_str())
                .is_some_and(|v| v == id)
        });
        if let Some(pos) = pos {
            arr.remove(pos);
        }
    }
}

async fn cmd_sample_stare(api: &CloudnetApi, add: bool) -> Result<(), String> {
    eprintln!("Fetching doppler-lidar product metadata...");
    let mut records = api.get_product_files("doppler-lidar").await?;
    eprintln!("Fetched {} records", records.len());

    if records.is_empty() {
        return Err("no doppler-lidar records found".to_string());
    }

    records.sort_by_key(|r| r.size.parse::<u64>().unwrap_or(0));
    let n = records.len();

    let mut entries = Vec::new();
    eprintln!();
    eprintln!(
        "  {:<8} {:<6} {:<20} {:<12} {:<12}",
        "ID", "Pctl", "Site", "Date", "Size"
    );
    eprintln!("  {}", "-".repeat(62));

    for &(label, p) in PERCENTILES {
        let idx = (n * usize::from(p) / 100).min(n - 1);
        let rec = &records[idx];
        let size: u64 = rec.size.parse().unwrap_or(0);
        let id = generate_id();

        eprintln!(
            "  {:<8} {:<6} {:<20} {:<12} {:<12}",
            id,
            label,
            rec.site.id,
            rec.measurement_date,
            format_size(size),
        );

        entries.push(BenchEntry {
            id,
            site: rec.site.id.clone(),
            date: rec.measurement_date.clone(),
            instrument_id: rec.instrument.instrument_id.clone(),
            instrument_uuid: rec.instrument.uuid.clone(),
            percentile: Some(label.to_string()),
            description: Some("added by dopbench sample".to_string()),
        });
    }

    if add {
        let path = bench_config_path();
        let text = fs::read_to_string(&path).unwrap_or_default();
        let mut doc: DocumentMut = text
            .parse()
            .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

        if doc.get("stare").is_none() {
            doc.insert("stare", Item::ArrayOfTables(ArrayOfTables::new()));
        }
        let arr = doc["stare"]
            .as_array_of_tables_mut()
            .ok_or("'stare' is not an array of tables in bench.toml")?;

        for entry in &entries {
            let mut t = Table::new();
            t.insert("id", value(&entry.id));
            t.insert("site", value(&entry.site));
            t.insert("date", value(&entry.date));
            t.insert("instrument_id", value(&entry.instrument_id));
            t.insert("instrument_uuid", value(&entry.instrument_uuid));
            if let Some(p) = &entry.percentile {
                t.insert("percentile", value(p));
            }
            if let Some(d) = &entry.description {
                t.insert("description", value(d));
            }
            arr.push(t);
        }

        fs::write(&path, doc.to_string())
            .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

        eprintln!();
        eprintln!("Wrote {}", path.display());
    }
    Ok(())
}

async fn fetch_and_download(
    api: &CloudnetApi,
    entry: &BenchEntry,
) -> Result<Vec<RawRecord>, String> {
    let records = if let Some(cached) = load_cached_records(&entry.id) {
        cached
    } else {
        let recs = api
            .get_raw_files_for_instrument(&entry.site, &entry.date, &entry.instrument_uuid)
            .await?;
        store_cached_records(&entry.id, &recs)?;
        recs
    };

    let mut downloaded = 0u32;
    for rec in &records {
        if has_cached_file(&rec.uuid) {
            continue;
        }
        let bytes = api.download_bytes(&rec.download_url).await?;
        let content = decompress_if_gz(&rec.filename, bytes)?;
        store_cached_file(&rec.uuid, &content)?;
        downloaded += 1;
    }
    if downloaded > 0 {
        eprintln!("  downloaded {downloaded} file(s)");
    }

    Ok(records)
}

fn doppy_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

fn os_version() -> String {
    let output = std::process::Command::new("uname").arg("-sr").output();
    match output {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).trim().to_string(),
        _ => "unknown".to_string(),
    }
}

fn cpu_model() -> String {
    #[cfg(target_os = "macos")]
    {
        let output = std::process::Command::new("sysctl")
            .args(["-n", "machdep.cpu.brand_string"])
            .output();
        if let Ok(o) = output
            && o.status.success()
        {
            return String::from_utf8_lossy(&o.stdout).trim().to_string();
        }
    }
    #[cfg(target_os = "linux")]
    {
        if let Ok(cpuinfo) = fs::read_to_string("/proc/cpuinfo") {
            for line in cpuinfo.lines() {
                if let Some(model) = line.strip_prefix("model name") {
                    if let Some(value) = model.trim_start().strip_prefix(':') {
                        return value.trim().to_string();
                    }
                }
            }
        }
    }
    "unknown".to_string()
}

fn build_lock_meta() -> LockMeta {
    LockMeta {
        locked_at: chrono::Utc::now().to_rfc3339(),
        doppy_version: doppy_version(),
    }
}

fn build_run_meta() -> RunMeta {
    RunMeta {
        date: chrono::Utc::now().to_rfc3339(),
        doppy_version: doppy_version(),
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        os_version: os_version(),
        cpu: cpu_model(),
    }
}

fn write_bench_lock(lock: &BenchLock) -> Result<(), String> {
    let lock_str = toml::to_string_pretty(lock).map_err(|e| format!("TOML error: {e}"))?;
    let header = "# bench.lock \u{2014} auto-generated by `dopbench`\n# DO NOT EDIT.\n\n";
    let lock_path = bench_lock_path();
    fs::write(&lock_path, format!("{header}{lock_str}"))
        .map_err(|e| format!("failed to write {}: {e}", lock_path.display()))?;
    eprintln!("Wrote {}", lock_path.display());
    Ok(())
}

fn build_lock_entry(
    entry: &BenchEntry,
    records: &[RawRecord],
    elapsed_secs: Option<f64>,
) -> Result<LockEntry, String> {
    let input_files: Vec<InputFile> = records
        .iter()
        .map(|r| {
            let hash = file_sha256(&cache_file_path(&r.uuid))?;
            Ok(InputFile {
                filename: r.filename.clone(),
                uuid: r.uuid.clone(),
                sha256: hash,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    Ok(LockEntry {
        id: entry.id.clone(),
        site: entry.site.clone(),
        date: entry.date.clone(),
        instrument_uuid: entry.instrument_uuid.clone(),
        elapsed_secs,
        input: LockInput { files: input_files },
    })
}

fn build_bench_payload(entry: &BenchEntry, records: &[RawRecord]) -> Result<String, String> {
    let local_records = build_local_records(records)?;
    let payload = serde_json::json!({
        "product": "stare",
        "site": entry.site,
        "date": entry.date,
        "instrument_id": entry.instrument_id,
        "instrument_uuid": entry.instrument_uuid,
        "records": local_records,
    });
    serde_json::to_string(&payload).map_err(|e| format!("serialize error: {e}"))
}

async fn run_bench_helper(entry: &BenchEntry, records: &[RawRecord]) -> Result<f64, String> {
    let json_str = build_bench_payload(entry, records)?;

    let python = python_path();
    let output = tokio::process::Command::new(&python)
        .args(["-m", "tests.helpers.bench_helper", &json_str])
        .output()
        .await
        .map_err(|e| format!("failed to spawn {python}: {e}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("bench_helper failed for {}: {stderr}", entry.id));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&stdout)
        .map_err(|e| format!("parse bench_helper output: {e}\n{stdout}"))?;
    result["elapsed_secs"]
        .as_f64()
        .ok_or_else(|| "missing elapsed_secs in bench_helper output".to_string())
}

async fn cmd_lock(
    api: &CloudnetApi,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
) -> Result<(), String> {
    let config = read_config()?;
    let entries = filter_entries(&config.stare, site_filter, id_filter);

    if entries.is_empty() {
        return Err("no stare entries match the given filters in bench.toml".to_string());
    }

    let total = entries.len();
    let mut lock_entries = Vec::new();

    for (i, entry) in entries.iter().enumerate() {
        eprintln!("[{}/{}] {} ...", i + 1, total, entry);
        let records = fetch_and_download(api, entry).await?;
        lock_entries.push(build_lock_entry(entry, &records, None)?);
    }

    let lock = BenchLock {
        meta: build_lock_meta(),
        run: None,
        stare: lock_entries,
    };
    write_bench_lock(&lock)?;

    Ok(())
}

async fn cmd_run(
    api: &CloudnetApi,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    save: bool,
) -> Result<(), String> {
    let config = read_config()?;
    let entries = filter_entries(&config.stare, site_filter, id_filter);

    if entries.is_empty() {
        return Err("no stare entries match the given filters in bench.toml".to_string());
    }

    let total = entries.len();
    let mut lock_entries = Vec::new();
    let mut results = Vec::new();

    for (i, entry) in entries.iter().enumerate() {
        eprint!("[{}/{}] {} ... ", i + 1, total, entry);

        let records = fetch_and_download(api, entry).await?;
        let elapsed = run_bench_helper(entry, &records).await?;

        if save {
            lock_entries.push(build_lock_entry(entry, &records, Some(elapsed))?);
        }

        eprintln!("{}", colored_time(elapsed));
        results.push((*entry, elapsed));
    }

    if save {
        let lock = BenchLock {
            meta: build_lock_meta(),
            run: Some(build_run_meta()),
            stare: lock_entries,
        };
        eprintln!();
        write_bench_lock(&lock)?;
    }

    // Print results table
    eprintln!();
    eprintln!("Benchmark results:");
    eprintln!();
    eprintln!(
        "  {:<8} {:<6} {:<20} {:<12} {:<10}",
        "ID", "Pctl", "Site", "Date", "Time"
    );
    eprintln!("  {}", "-".repeat(58));
    for (entry, elapsed) in &results {
        let pctl = entry.percentile.as_deref().unwrap_or("-");
        eprintln!(
            "  \x1b[36m{:<8}\x1b[0m {:<6} {:<20} {:<12} {}",
            entry.id,
            pctl,
            entry.site,
            entry.date,
            colored_time(*elapsed),
        );
    }

    Ok(())
}

fn colored_time(secs: f64) -> String {
    let color = if secs < 1.0 {
        "\x1b[32m" // green
    } else if secs < 10.0 {
        "\x1b[34m" // blue
    } else if secs < 30.0 {
        "\x1b[33m" // yellow
    } else {
        "\x1b[31m" // red
    };
    format!("{color}{secs:.2}s\x1b[0m")
}

fn is_py_spy_available() -> bool {
    std::process::Command::new("py-spy")
        .arg("--version")
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .is_ok_and(|s| s.success())
}

fn open_file(path: &Path) -> Result<(), String> {
    let cmd = if cfg!(target_os = "macos") {
        "open"
    } else if cfg!(target_os = "windows") {
        "start"
    } else {
        "xdg-open"
    };
    std::process::Command::new(cmd)
        .arg(path)
        .spawn()
        .map_err(|e| format!("failed to open {}: {e}", path.display()))?;
    Ok(())
}

/// Returns `Ok(true)` on success, `Ok(false)` if py-spy failed with a known
/// recoverable error (permissions, unsupported Python version).
async fn run_py_spy(
    json_str: &str,
    output_path: &Path,
    format: &ProfileFormat,
    native: bool,
) -> Result<bool, String> {
    let mut args = vec![
        "record".to_string(),
        "-o".to_string(),
        output_path.to_string_lossy().to_string(),
        "-f".to_string(),
        format.py_spy_flag().to_string(),
    ];
    if native {
        args.push("--native".to_string());
    }
    args.extend([
        "--".to_string(),
        python_path(),
        "-m".to_string(),
        "tests.helpers.bench_helper".to_string(),
        json_str.to_string(),
    ]);

    let output = tokio::process::Command::new("py-spy")
        .args(&args)
        .output()
        .await
        .map_err(|e| format!("failed to spawn py-spy: {e}"))?;

    if output.status.success() {
        return Ok(true);
    }

    let stderr = String::from_utf8_lossy(&output.stderr);
    let hint = if stderr.contains("requires root") || stderr.contains("elevated permissions") {
        "py-spy requires root on macOS"
    } else if stderr.contains("python version") {
        "py-spy doesn't support this Python version"
    } else {
        return Err(format!("py-spy failed: {stderr}"));
    };
    eprintln!("{hint}, falling back to cProfile");
    Ok(false)
}

async fn run_cprofile(json_str: &str, output_path: &Path) -> Result<(), String> {
    let python = python_path();
    let output_str = output_path.to_string_lossy().to_string();
    let output = tokio::process::Command::new(&python)
        .args(["-m", "tests.helpers.profile_helper", json_str, &output_str])
        .output()
        .await
        .map_err(|e| format!("failed to spawn {python}: {e}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("profile_helper failed: {stderr}"));
    }
    Ok(())
}

async fn cmd_profile(
    api: &CloudnetApi,
    id: &str,
    profiler: Profiler,
    format: ProfileFormat,
    output: Option<String>,
    native: bool,
    open: bool,
) -> Result<(), String> {
    let config = read_config()?;
    let entries = filter_entries(&config.stare, None, Some(id));
    let entry = entries
        .into_iter()
        .next()
        .ok_or_else(|| format!("no entry found with id '{id}'"))?;

    eprintln!("Profiling {entry} ...");

    let records = fetch_and_download(api, entry).await?;
    let json_str = build_bench_payload(entry, &records)?;

    let actual_profiler = match profiler {
        Profiler::PySpy if !is_py_spy_available() => {
            eprintln!("py-spy not found, falling back to cProfile");
            Profiler::Cprofile
        }
        other => other,
    };

    let prof_dir = profiles_dir();
    fs::create_dir_all(&prof_dir).map_err(|e| format!("failed to create profiles dir: {e}"))?;

    let output_path = match (&actual_profiler, &output) {
        (_, Some(custom)) => PathBuf::from(custom),
        (Profiler::PySpy, None) => prof_dir.join(format!("{id}.{}", format.extension())),
        (Profiler::Cprofile, None) => prof_dir.join(format!("{id}.prof")),
    };

    match actual_profiler {
        Profiler::PySpy => {
            if !run_py_spy(&json_str, &output_path, &format, native).await? {
                let fallback_path =
                    output.map_or_else(|| prof_dir.join(format!("{id}.prof")), PathBuf::from);
                run_cprofile(&json_str, &fallback_path).await?;
                eprintln!("Profile saved to {}", fallback_path.display());
                if open {
                    open_file(&fallback_path)?;
                }
                return Ok(());
            }
        }
        Profiler::Cprofile => {
            run_cprofile(&json_str, &output_path).await?;
        }
    }

    eprintln!("Profile saved to {}", output_path.display());

    if open {
        open_file(&output_path)?;
    }

    Ok(())
}

// ── Main ────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    let result = run().await;
    if let Err(e) = result {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

async fn run() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Command::Add { product } => {
            let api = CloudnetApi::new()?;
            cmd_add(&api, product).await
        }
        Command::List { site, id } => cmd_list(site.as_deref(), id.as_deref()),
        Command::Remove { id } => cmd_remove(&id),
        Command::Sample { product } => {
            let api = CloudnetApi::new()?;
            match product {
                SampleProduct::Stare { add } => cmd_sample_stare(&api, add).await,
            }
        }
        Command::Lock { site, id } => {
            let api = CloudnetApi::new()?;
            cmd_lock(&api, site.as_deref(), id.as_deref()).await
        }
        Command::Run { site, id, save } => {
            let api = CloudnetApi::new()?;
            cmd_run(&api, site.as_deref(), id.as_deref(), save).await
        }
        Command::Profile {
            id,
            profiler,
            format,
            output,
            native,
            open,
        } => {
            let api = CloudnetApi::new()?;
            cmd_profile(&api, &id, profiler, format, output, native, open).await
        }
    }
}

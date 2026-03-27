use std::collections::{HashMap, HashSet};
use std::fmt::Write as _;
use std::fs;
use std::io::Read as _;
use std::path::{Path, PathBuf};
use std::time::Duration;

use chrono::{NaiveDate, Utc};
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

#[derive(Clone, clap::ValueEnum)]
enum BenchKind {
    Stare,
    Raw,
}

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
        /// Run only stare or raw entries
        #[arg(long, value_enum)]
        kind: Option<BenchKind>,
        /// Re-lock all entries from scratch
        #[arg(long)]
        update_all: bool,
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
        /// Run only stare or raw entries
        #[arg(long, value_enum)]
        kind: Option<BenchKind>,
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
    /// Sample raw halo-doppler-lidar files by size percentile
    Raw {
        /// Add selected samples to bench.toml
        #[arg(long)]
        add: bool,
        /// Re-fetch metadata cache
        #[arg(long)]
        force: bool,
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

#[derive(Debug, Clone, Serialize, Deserialize)]
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
    instrument: InstrumentRef,
    #[serde(default)]
    tags: Vec<String>,
}

/// API response for `/raw-files` when fetching with date ranges (sampling).
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RawFileRecord {
    uuid: String,
    filename: String,
    measurement_date: String,
    site: SiteRef,
    size: String,
    instrument: InstrumentRef,
}

/// Flattened raw file record for rkyv caching.
#[derive(Debug, Clone, rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)]
struct CachedRawRecord {
    uuid: String,
    filename: String,
    measurement_date: String,
    site_id: String,
    instrument_id: String,
    instrument_uuid: String,
    size: u64,
}

impl From<RawFileRecord> for CachedRawRecord {
    fn from(r: RawFileRecord) -> Self {
        Self {
            uuid: r.uuid,
            filename: r.filename,
            measurement_date: r.measurement_date,
            site_id: r.site.id,
            instrument_id: r.instrument.instrument_id,
            instrument_uuid: r.instrument.uuid,
            size: r.size.parse().unwrap_or(0),
        }
    }
}

// ── TOML types ──────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct BenchConfig {
    #[serde(default)]
    stare: Vec<BenchEntry>,
    #[serde(default)]
    raw: Vec<RawBenchEntry>,
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

#[derive(Debug, Serialize, Deserialize)]
struct RawBenchEntry {
    id: String,
    instrument_id: String,
    instrument_uuid: String,
    site: String,
    date: String,
    filename: String,
    file_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    percentile: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    description: Option<String>,
}

impl std::fmt::Display for RawBenchEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "[\x1b[36m{}\x1b[0m] raw {} {} {}",
            self.id, self.site, self.date, self.filename,
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

#[derive(Debug, Default, Serialize, Deserialize)]
struct BenchLock {
    #[serde(default)]
    meta: LockMeta,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    run: Option<RunMeta>,
    #[serde(default)]
    stare: Vec<LockEntry>,
    #[serde(default)]
    raw: Vec<RawLockEntry>,
}

impl BenchLock {
    fn locked_ids(&self) -> HashSet<&str> {
        self.stare
            .iter()
            .map(|e| e.id.as_str())
            .chain(self.raw.iter().map(|e| e.id.as_str()))
            .collect()
    }
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

#[derive(Debug, Serialize, Deserialize)]
struct RawLockEntry {
    id: String,
    site: String,
    date: String,
    instrument_uuid: String,
    filename: String,
    file_uuid: String,
    sha256: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    elapsed_secs: Option<f64>,
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

trait HasIdAndSite {
    fn id(&self) -> &str;
    fn site(&self) -> &str;
    fn percentile(&self) -> Option<&str>;
    fn date(&self) -> &str;
    fn result_label(&self) -> &'static str;
    fn extra_columns(&self) -> Option<(&str, String)> {
        None
    }
}

impl HasIdAndSite for BenchEntry {
    fn id(&self) -> &str {
        &self.id
    }
    fn site(&self) -> &str {
        &self.site
    }
    fn percentile(&self) -> Option<&str> {
        self.percentile.as_deref()
    }
    fn date(&self) -> &str {
        &self.date
    }
    fn result_label(&self) -> &'static str {
        "Stare"
    }
}

impl HasIdAndSite for RawBenchEntry {
    fn id(&self) -> &str {
        &self.id
    }
    fn site(&self) -> &str {
        &self.site
    }
    fn percentile(&self) -> Option<&str> {
        self.percentile.as_deref()
    }
    fn date(&self) -> &str {
        &self.date
    }
    fn result_label(&self) -> &'static str {
        "Raw"
    }
    fn extra_columns(&self) -> Option<(&str, String)> {
        Some(("Filename", self.filename.clone()))
    }
}

fn filter_entries<'a, T: HasIdAndSite>(
    entries: &'a [T],
    site_filter: Option<&str>,
    id_filter: Option<&str>,
) -> Vec<&'a T> {
    entries
        .iter()
        .filter(|e| {
            site_filter.is_none_or(|s| e.site() == s) && id_filter.is_none_or(|id| e.id() == id)
        })
        .collect()
}

fn filter_by_kind<'a>(
    config: &'a BenchConfig,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    kind: Option<&BenchKind>,
) -> (Vec<&'a BenchEntry>, Vec<&'a RawBenchEntry>) {
    let stare = if matches!(kind, Some(BenchKind::Raw)) {
        vec![]
    } else {
        filter_entries(&config.stare, site_filter, id_filter)
    };
    let raw = if matches!(kind, Some(BenchKind::Stare)) {
        vec![]
    } else {
        filter_entries(&config.raw, site_filter, id_filter)
    };
    (stare, raw)
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
    let stare_filtered = filter_entries(&config.stare, site_filter, id_filter);
    let raw_filtered = filter_entries(&config.raw, site_filter, id_filter);

    let total = stare_filtered.len() + raw_filtered.len();
    if total == 0 {
        println!("No entries match the given filters.");
        return Ok(());
    }

    println!("{total} entry(ies):\n");
    for entry in &stare_filtered {
        println!("  {entry}");
    }
    for entry in &raw_filtered {
        println!("  {entry}");
    }
    Ok(())
}

fn cmd_remove(id: &str) -> Result<(), String> {
    let config = read_config()?;
    let stare_entry = config.stare.iter().find(|e| e.id == id);
    let raw_entry = config.raw.iter().find(|e| e.id == id);

    match (&stare_entry, &raw_entry) {
        (None, None) => return Err(format!("no entry found with id '{id}'")),
        (Some(e), _) => println!("  {e}"),
        (_, Some(e)) => println!("  {e}"),
    }

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
    remove_from_toml_array(&mut doc, "raw", id);
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
        remove_from_toml_array(&mut lock_doc, "raw", id);
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

// ── Raw sampling: monthly-batched fetch + rkyv cache ────────────────

fn raw_cache_path() -> PathBuf {
    cache_dir().join("raw-files.rkyv")
}

fn weekly_intervals() -> Vec<(NaiveDate, NaiveDate)> {
    let today = Utc::now().date_naive();
    let start = NaiveDate::from_ymd_opt(2010, 1, 1).unwrap();

    let mut intervals = Vec::new();
    let mut cursor = start;
    while cursor < today {
        let next = cursor + chrono::Duration::days(7);
        intervals.push((cursor, next.min(today)));
        cursor = next;
    }

    intervals
}

async fn fetch_raw_files_for_interval(
    api: &CloudnetApi,
    instrument: &str,
    date_from: NaiveDate,
    date_to: NaiveDate,
) -> Result<Vec<RawFileRecord>, String> {
    let from = date_from.to_string();
    let to = date_to.to_string();

    let url = reqwest::Url::parse_with_params(
        &format!("{BASE_URL}/raw-files"),
        &[
            ("instrument", instrument),
            ("filenameSuffix", ".hpl"),
            ("dateFrom", &from),
            ("dateTo", &to),
        ],
    )
    .map_err(|e| format!("invalid URL params: {e}"))?;

    api.get_json(url.as_str()).await
}

async fn load_or_fetch_raw_cache(force: bool) -> Result<Vec<CachedRawRecord>, String> {
    let path = raw_cache_path();

    if !force && path.exists() {
        let bytes = fs::read(&path).map_err(|e| format!("failed to read cache: {e}"))?;
        let records: Vec<CachedRawRecord> =
            rkyv::from_bytes::<Vec<CachedRawRecord>, rkyv::rancor::Error>(&bytes)
                .map_err(|e| format!("failed to deserialize cache: {e}"))?;
        eprintln!("{} records loaded from cache.", records.len());
        return Ok(records);
    }

    let api = CloudnetApi::new()?;
    let instrument = "halo-doppler-lidar";

    let intervals = weekly_intervals();
    let total = intervals.len();
    let mut all_records: Vec<CachedRawRecord> = Vec::new();

    eprintln!("Fetching {instrument} raw file metadata...");
    for (i, (from, to)) in intervals.iter().enumerate() {
        eprint!("\r  [{}/{}] ", i + 1, total);
        match fetch_raw_files_for_interval(&api, instrument, *from, *to).await {
            Ok(records) => {
                all_records.extend(records.into_iter().map(CachedRawRecord::from));
            }
            Err(e) => {
                eprintln!("error: {e}");
            }
        }
    }
    eprintln!("\r  -> {} records", all_records.len());

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("failed to create cache dir: {e}"))?;
    }
    let bytes = rkyv::to_bytes::<rkyv::rancor::Error>(&all_records)
        .map_err(|e| format!("failed to serialize: {e}"))?;
    fs::write(&path, &bytes).map_err(|e| format!("failed to write cache: {e}"))?;

    eprintln!("Cached to {}", path.display());
    Ok(all_records)
}

async fn cmd_sample_raw(add: bool, force: bool) -> Result<(), String> {
    let records = load_or_fetch_raw_cache(force).await?;

    if records.is_empty() {
        return Err("no halo-doppler-lidar raw records found".to_string());
    }

    let mut sorted: Vec<&CachedRawRecord> = records.iter().collect();
    sorted.sort_by_key(|r| r.size);
    let n = sorted.len();

    let mut entries = Vec::new();
    eprintln!();
    eprintln!(
        "  {:<8} {:<6} {:<20} {:<12} {:<30} {:<12}",
        "ID", "Pctl", "Site", "Date", "Filename", "Size"
    );
    eprintln!("  {}", "-".repeat(90));

    for &(label, p) in PERCENTILES {
        let idx = (n * usize::from(p) / 100).min(n - 1);
        let rec = sorted[idx];
        let id = generate_id();

        eprintln!(
            "  {:<8} {:<6} {:<20} {:<12} {:<30} {:<12}",
            id,
            label,
            rec.site_id,
            rec.measurement_date,
            rec.filename,
            format_size(rec.size),
        );

        entries.push(RawBenchEntry {
            id,
            instrument_id: rec.instrument_id.clone(),
            instrument_uuid: rec.instrument_uuid.clone(),
            site: rec.site_id.clone(),
            date: rec.measurement_date.clone(),
            filename: rec.filename.clone(),
            file_uuid: rec.uuid.clone(),
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

        if doc.get("raw").is_none() {
            doc.insert("raw", Item::ArrayOfTables(ArrayOfTables::new()));
        }
        let arr = doc["raw"]
            .as_array_of_tables_mut()
            .ok_or("'raw' is not an array of tables in bench.toml")?;

        for entry in &entries {
            let mut t = Table::new();
            t.insert("id", value(&entry.id));
            t.insert("instrument_id", value(&entry.instrument_id));
            t.insert("instrument_uuid", value(&entry.instrument_uuid));
            t.insert("site", value(&entry.site));
            t.insert("date", value(&entry.date));
            t.insert("filename", value(&entry.filename));
            t.insert("file_uuid", value(&entry.file_uuid));
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

async fn fetch_and_download_single_raw(
    api: &CloudnetApi,
    entry: &RawBenchEntry,
) -> Result<(), String> {
    if has_cached_file(&entry.file_uuid) {
        return Ok(());
    }
    let url = format!(
        "{BASE_URL}/download/raw/{}/{}",
        entry.file_uuid, entry.filename
    );
    let bytes = api.download_bytes(&url).await?;
    let content = decompress_if_gz(&entry.filename, bytes)?;
    store_cached_file(&entry.file_uuid, &content)?;
    eprintln!("  downloaded {}", entry.filename);
    Ok(())
}

fn build_raw_lock_entry(
    entry: &RawBenchEntry,
    elapsed_secs: Option<f64>,
) -> Result<RawLockEntry, String> {
    let sha256 = file_sha256(&cache_file_path(&entry.file_uuid))?;
    Ok(RawLockEntry {
        id: entry.id.clone(),
        site: entry.site.clone(),
        date: entry.date.clone(),
        instrument_uuid: entry.instrument_uuid.clone(),
        filename: entry.filename.clone(),
        file_uuid: entry.file_uuid.clone(),
        sha256,
        elapsed_secs,
    })
}

fn run_raw_bench(entry: &RawBenchEntry) -> Result<f64, String> {
    let path = cache_file_path(&entry.file_uuid);
    let content = fs::read(&path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let start = std::time::Instant::now();
    doprs::raw::halo_hpl::from_bytes_src(&content)
        .map_err(|e| format!("parse failed for {}: {e}", entry.filename))?;
    Ok(start.elapsed().as_secs_f64())
}

// ── Fetch & download (stare) ────────────────────────────────────────

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

fn read_bench_lock() -> Option<BenchLock> {
    let text = fs::read_to_string(bench_lock_path()).ok()?;
    toml::from_str(&text).ok()
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
    kind: Option<&BenchKind>,
    update_all: bool,
) -> Result<(), String> {
    let config = read_config()?;
    let has_filter = site_filter.is_some() || id_filter.is_some() || kind.is_some();

    let mut lock = if update_all {
        BenchLock::default()
    } else {
        read_bench_lock().unwrap_or_default()
    };

    let (stare_entries, raw_entries) = if update_all || has_filter {
        filter_by_kind(&config, site_filter, id_filter, kind)
    } else {
        let locked = lock.locked_ids();
        let stare: Vec<_> = config
            .stare
            .iter()
            .filter(|e| !locked.contains(e.id()))
            .collect();
        let raw: Vec<_> = config
            .raw
            .iter()
            .filter(|e| !locked.contains(e.id()))
            .collect();
        (stare, raw)
    };

    if stare_entries.is_empty() && raw_entries.is_empty() {
        if !has_filter && !update_all {
            eprintln!("All entries already locked. Use --update-all to re-lock everything.");
        } else {
            return Err("no entries match the given filters in bench.toml".to_string());
        }
        return Ok(());
    }

    lock.meta = build_lock_meta();

    let total_stare = stare_entries.len();
    for (i, entry) in stare_entries.iter().enumerate() {
        eprintln!("[{}/{}] {} ...", i + 1, total_stare, entry);
        let records = fetch_and_download(api, entry).await?;
        let lock_entry = build_lock_entry(entry, &records, None)?;
        lock.stare.retain(|e| e.id != entry.id());
        lock.stare.push(lock_entry);
    }

    let total_raw = raw_entries.len();
    for (i, entry) in raw_entries.iter().enumerate() {
        eprintln!("[{}/{}] {} ...", i + 1, total_raw, entry);
        fetch_and_download_single_raw(api, entry).await?;
        let lock_entry = build_raw_lock_entry(entry, None)?;
        lock.raw.retain(|e| e.id != entry.id());
        lock.raw.push(lock_entry);
    }

    write_bench_lock(&lock)?;

    Ok(())
}

async fn cmd_run(
    api: &CloudnetApi,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    save: bool,
    kind: Option<&BenchKind>,
) -> Result<(), String> {
    let config = read_config()?;
    let (stare_entries, raw_entries) = filter_by_kind(&config, site_filter, id_filter, kind);

    if stare_entries.is_empty() && raw_entries.is_empty() {
        return Err("no entries match the given filters in bench.toml".to_string());
    }

    let old_elapsed = read_old_elapsed();
    let total_stare = stare_entries.len();
    let mut stare_lock_entries = Vec::new();
    let mut stare_results = Vec::new();

    for (i, entry) in stare_entries.iter().enumerate() {
        eprint!("[{}/{}] {} ... ", i + 1, total_stare, entry);

        let records = fetch_and_download(api, entry).await?;
        let elapsed = run_bench_helper(entry, &records).await?;

        if save {
            stare_lock_entries.push(build_lock_entry(entry, &records, Some(elapsed))?);
        }

        match old_elapsed.get(&entry.id) {
            Some(&old) => eprintln!("{} {}", colored_time(elapsed), format_speedup(old, elapsed)),
            None => eprintln!("{}", colored_time(elapsed)),
        }
        stare_results.push((*entry, elapsed));
    }

    let total_raw = raw_entries.len();
    let mut raw_lock_entries = Vec::new();
    let mut raw_results = Vec::new();

    for (i, entry) in raw_entries.iter().enumerate() {
        eprint!("[{}/{}] {} ... ", i + 1, total_raw, entry);

        fetch_and_download_single_raw(api, entry).await?;
        let elapsed = run_raw_bench(entry)?;

        if save {
            raw_lock_entries.push(build_raw_lock_entry(entry, Some(elapsed))?);
        }

        match old_elapsed.get(&entry.id) {
            Some(&old) => eprintln!("{} {}", colored_time(elapsed), format_speedup(old, elapsed)),
            None => eprintln!("{}", colored_time(elapsed)),
        }
        raw_results.push((*entry, elapsed));
    }

    if save {
        let lock = BenchLock {
            meta: build_lock_meta(),
            run: Some(build_run_meta()),
            stare: stare_lock_entries,
            raw: raw_lock_entries,
        };
        eprintln!();
        write_bench_lock(&lock)?;
    }

    print_results(&stare_results, &old_elapsed);
    print_results(&raw_results, &old_elapsed);

    Ok(())
}

fn print_results<T: HasIdAndSite>(results: &[(&T, f64)], old_elapsed: &HashMap<String, f64>) {
    if results.is_empty() {
        return;
    }
    let label = results[0].0.result_label();
    let has_extra = results[0].0.extra_columns().is_some();
    let has_baseline = results
        .iter()
        .any(|(e, _)| old_elapsed.contains_key(e.id()));

    eprintln!();
    eprintln!("{label} benchmark results:");
    eprintln!();

    let mut header = format!("  {:<8} {:<6} {:<20} {:<12} ", "ID", "Pctl", "Site", "Date");
    if has_extra {
        let _ = write!(header, "{:<30} ", results[0].0.extra_columns().unwrap().0);
    }
    let _ = write!(header, "{:<10}", "Time");
    if has_baseline {
        header.push_str(" Speedup");
    }
    eprintln!("{header}");
    eprintln!("  {}", "-".repeat(header.len() - 2));

    for (entry, elapsed) in results {
        let pctl = entry.percentile().unwrap_or("-");
        let speedup = old_elapsed
            .get(entry.id())
            .map(|&old| format_speedup(old, *elapsed))
            .unwrap_or_default();
        eprint!(
            "  \x1b[36m{:<8}\x1b[0m {:<6} {:<20} {:<12} ",
            entry.id(),
            pctl,
            entry.site(),
            entry.date(),
        );
        if let Some((_, val)) = entry.extra_columns() {
            eprint!("{val:<30} ");
        }
        eprintln!("{} {}", colored_time(*elapsed), speedup);
    }
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

fn read_old_elapsed() -> HashMap<String, f64> {
    let path = bench_lock_path();
    let Ok(text) = fs::read_to_string(path) else {
        return HashMap::new();
    };
    let Ok(lock) = toml::from_str::<BenchLock>(&text) else {
        return HashMap::new();
    };
    let mut map: HashMap<String, f64> = lock
        .stare
        .into_iter()
        .filter_map(|e| Some((e.id, e.elapsed_secs?)))
        .collect();
    for e in lock.raw {
        if let Some(elapsed) = e.elapsed_secs {
            map.insert(e.id, elapsed);
        }
    }
    map
}

fn format_speedup(old: f64, new: f64) -> String {
    let ratio = old / new;
    if ratio >= 1.0 {
        format!("\x1b[32m({ratio:.2}x faster)\x1b[0m")
    } else {
        let slowdown = 1.0 / ratio;
        format!("\x1b[31m({slowdown:.2}x slower)\x1b[0m")
    }
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
        Command::Sample { product } => match product {
            SampleProduct::Stare { add } => {
                let api = CloudnetApi::new()?;
                cmd_sample_stare(&api, add).await
            }
            SampleProduct::Raw { add, force } => cmd_sample_raw(add, force).await,
        },
        Command::Lock {
            site,
            id,
            kind,
            update_all,
        } => {
            let api = CloudnetApi::new()?;
            cmd_lock(
                &api,
                site.as_deref(),
                id.as_deref(),
                kind.as_ref(),
                update_all,
            )
            .await
        }
        Command::Run {
            site,
            id,
            save,
            kind,
        } => {
            let api = CloudnetApi::new()?;
            cmd_run(&api, site.as_deref(), id.as_deref(), save, kind.as_ref()).await
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

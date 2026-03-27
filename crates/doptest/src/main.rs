mod api;
mod cache;
mod cluster;
mod compare;
mod download;
mod features;
mod legacy;
mod python;
mod sample;
mod types;

use std::fs;
use std::path::{Path, PathBuf};

use fs2::FileExt;

use clap::{Parser, Subcommand};
use toml_edit::{ArrayOfTables, DocumentMut, Item, Table, value};

use api::CloudnetApi;
use cache::FileCache;
use types::{FileType, RawKind, TestsConfig, TestsLock, generate_id};

// ── CLI ─────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(name = "doptest", about = "Doppy test framework")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Add a new test case to tests.toml
    Add {
        #[command(subcommand)]
        product: AddProduct,
    },
    /// List all tests from tests.toml
    List {
        /// Filter by product type
        #[arg(long)]
        product: Option<String>,
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// List only the test with this id
        id: Option<String>,
    },
    /// Verify tests.toml and tests.lock are consistent
    Check,
    /// Download test files to local cache
    Download {
        /// Filter by product type
        #[arg(long)]
        product: Option<String>,
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Download only the test with this id
        id: Option<String>,
        /// Force re-download even if cached
        #[arg(long)]
        force: bool,
    },
    /// Generate or update tests.lock
    Lock {
        /// Filter by product type
        #[arg(long)]
        product: Option<String>,
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Update only the test with this id
        id: Option<String>,
        /// Re-lock all tests from scratch
        #[arg(long, conflicts_with_all = ["product", "site", "id"])]
        update_all: bool,
    },
    /// Sample product files from Cloudnet
    Sample {
        #[command(subcommand)]
        action: SampleAction,
    },
    /// Remove a test case by id
    Remove {
        /// The test id to remove
        id: String,
    },
    /// Remove cached files
    Clean,
    /// Run tests against expectations in tests.lock
    Run {
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Filter by product type
        #[arg(long)]
        product: Option<String>,
        /// Filter by kind (same as product)
        #[arg(long)]
        kind: Option<String>,
        /// Exclude tests from these sites
        #[arg(long)]
        exclude_site: Vec<String>,
        /// Run only the test with this id
        id: Option<String>,
    },
    /// Run or list legacy tests from tests-legacy.toml
    Legacy {
        #[command(subcommand)]
        action: LegacyAction,
    },
}

#[derive(Subcommand)]
enum LegacyAction {
    /// Run legacy tests (shells out to python -m tests)
    Run {
        /// Filter by category: raw or product
        #[arg(long)]
        category: Option<String>,
        /// Filter by product name substring
        #[arg(long)]
        product: Option<String>,
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Filter by test source (e.g., '`raw.halo_hpl`')
        #[arg(long)]
        source: Option<String>,
        /// Run a specific test by ID
        #[arg(long)]
        id: Option<String>,
        /// Include slow tests
        #[arg(long)]
        include_slow: bool,
    },
    /// List legacy tests from tests-legacy.toml
    List {
        /// Filter by category: raw or product
        #[arg(long)]
        category: Option<String>,
        /// Filter by product name substring
        #[arg(long)]
        product: Option<String>,
        /// Filter by site
        #[arg(long)]
        site: Option<String>,
        /// Filter by test source (e.g., '`raw.halo_hpl`')
        #[arg(long)]
        source: Option<String>,
        /// List a specific test by ID
        #[arg(long)]
        id: Option<String>,
        /// Include slow tests in listing
        #[arg(long)]
        include_slow: bool,
    },
}

#[derive(Subcommand)]
enum AddProduct {
    /// Add a Stare test
    Stare {
        site: String,
        date: String,
        instrument_uuid: Option<String>,
        #[arg(long)]
        description: Option<String>,
    },
    /// Add a Wind test
    Wind {
        site: String,
        date: String,
        instrument_uuid: Option<String>,
        #[arg(long)]
        ftype: Option<FileType>,
        #[arg(long)]
        azimuth_offset_deg: Option<f64>,
        #[arg(long)]
        description: Option<String>,
    },
    /// Add a `StareDepol` test
    StareDepol {
        site: String,
        date: String,
        #[arg(long)]
        description: Option<String>,
    },
    /// Add a Turbulence test
    Turbulence {
        site: String,
        date: String,
        instrument_uuid: Option<String>,
        #[arg(long)]
        description: Option<String>,
    },
    /// Add a Raw test
    Raw {
        kind: RawKind,
        site: String,
        date: String,
        #[arg(long)]
        filename: Option<String>,
        #[arg(long)]
        uuid: Option<String>,
        #[arg(long)]
        prefix: Option<String>,
        #[arg(long)]
        suffix: Option<String>,
        #[arg(long)]
        ftype: Option<FileType>,
        #[arg(long)]
        description: Option<String>,
    },
}

#[derive(Subcommand)]
enum SampleAction {
    /// Fetch and cache product file metadata from Cloudnet API
    Fetch {
        /// Re-fetch everything, ignoring cache
        #[arg(long)]
        force: bool,
    },
    /// Sample stare product files (doppler-lidar)
    Stare {
        /// Number of files to sample per (site, instrument) pair
        #[arg(short, long, default_value_t = 10)]
        n: usize,
        /// Re-fetch cache before sampling
        #[arg(long)]
        force: bool,
        /// Files to select per cluster (default: 1)
        #[arg(long, default_value_t = 1)]
        per_cluster: usize,
        /// Add selected samples to tests.toml
        #[arg(long)]
        add: bool,
    },
    /// Sample wind product files (doppler-lidar-wind)
    Wind {
        /// Number of files to sample per (site, instrument) pair
        #[arg(short, long, default_value_t = 10)]
        n: usize,
        /// Re-fetch cache before sampling
        #[arg(long)]
        force: bool,
        /// Files to select per cluster (default: 1)
        #[arg(long, default_value_t = 1)]
        per_cluster: usize,
        /// Add selected samples to tests.toml
        #[arg(long)]
        add: bool,
    },
    /// Sample turbulence product files (epsilon-lidar)
    Turbulence {
        /// Number of files to sample per (site, instrument) pair
        #[arg(short, long, default_value_t = 10)]
        n: usize,
        /// Re-fetch cache before sampling
        #[arg(long)]
        force: bool,
        /// Files to select per cluster (default: 1)
        #[arg(long, default_value_t = 1)]
        per_cluster: usize,
        /// Add selected samples to tests.toml
        #[arg(long)]
        add: bool,
    },
}

// ── Paths ───────────────────────────────────────────────────────────

fn tests_dir() -> PathBuf {
    Path::new("tests").to_path_buf()
}

fn config_path() -> PathBuf {
    tests_dir().join("tests.toml")
}

fn lock_path() -> PathBuf {
    tests_dir().join("tests.lock")
}

fn cache_dir() -> PathBuf {
    tests_dir().join(".cache")
}

fn write_lock(lock: &TestsLock) -> Result<(), String> {
    let path = lock_path();
    let header = "# tests.lock — auto-generated by `doptest lock`\n# DO NOT EDIT. Regenerate with: doptest lock\n\n";
    let body =
        toml::to_string_pretty(lock).map_err(|e| format!("failed to serialize lock: {e}"))?;
    fs::write(&path, format!("{header}{body}"))
        .map_err(|e| format!("failed to write {}: {e}", path.display()))
}

fn acquire_lock_file() -> Result<fs::File, String> {
    let flock_path = tests_dir().join(".tests.lock.flock");
    let file = fs::OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(false)
        .open(&flock_path)
        .map_err(|e| format!("failed to open lock file: {e}"))?;
    file.try_lock_exclusive()
        .map_err(|_| "Another `doptest lock` process is already running.".to_string())?;
    Ok(file)
}

fn read_config() -> Result<TestsConfig, String> {
    let path = config_path();
    let text =
        fs::read_to_string(&path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    toml::from_str(&text).map_err(|e| format!("failed to parse {}: {e}", path.display()))
}

fn read_lock() -> Result<TestsLock, String> {
    let path = lock_path();
    let text =
        fs::read_to_string(&path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    toml::from_str(&text).map_err(|e| format!("failed to parse {}: {e}", path.display()))
}

fn doppy_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

// ── Filter helper ───────────────────────────────────────────────────

fn filter_entries(
    entries: Vec<types::TestEntry>,
    product_filter: Option<&str>,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    exclude_sites: &[String],
) -> Vec<types::TestEntry> {
    entries
        .into_iter()
        .filter(|e| {
            product_filter.is_none_or(|p| e.product() == p)
                && site_filter.is_none_or(|s| e.site() == s)
                && id_filter.is_none_or(|id| e.id() == id)
                && !exclude_sites.iter().any(|s| e.site() == s)
        })
        .collect()
}

// ── Add command ─────────────────────────────────────────────────────

struct ResolvedInstrument {
    instrument_id: String,
    instrument_uuid: String,
}

async fn resolve_instrument(site: &str, date: &str) -> Result<ResolvedInstrument, String> {
    let api = CloudnetApi::new()?;
    let records = api.get_raw_records(site, date).await?;

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
            Ok(ResolvedInstrument {
                instrument_id,
                instrument_uuid: uuid,
            })
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
    site: &str,
    date: &str,
    instrument_uuid: &str,
) -> Result<String, String> {
    let api = CloudnetApi::new()?;
    let records = api
        .get_records_by_instrument_uuid(site, instrument_uuid, date)
        .await?;
    records
        .first()
        .map(|r| r.instrument.instrument_id.clone())
        .ok_or_else(|| {
            format!("no records found for instrument {instrument_uuid} at {site} on {date}")
        })
}

#[allow(clippy::too_many_lines)]
async fn cmd_add(product: AddProduct) -> Result<(), String> {
    let path = config_path();
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
            description,
        } => {
            validate_date(&date)?;
            let (instrument_id, instrument_uuid) = if let Some(uuid) = instrument_uuid {
                let id = resolve_instrument_id(&site, &date, &uuid).await?;
                (id, uuid)
            } else {
                let r = resolve_instrument(&site, &date).await?;
                (r.instrument_id, r.instrument_uuid)
            };
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            t.insert("instrument_id", value(&instrument_id));
            t.insert("instrument_uuid", value(&instrument_uuid));
            if let Some(r) = &description {
                t.insert("description", value(r));
            }
            ("stare", t)
        }
        AddProduct::Wind {
            site,
            date,
            instrument_uuid,
            ftype,
            azimuth_offset_deg,
            description,
        } => {
            validate_date(&date)?;
            let (instrument_id, instrument_uuid) = if let Some(uuid) = instrument_uuid {
                let id = resolve_instrument_id(&site, &date, &uuid).await?;
                (id, uuid)
            } else {
                let r = resolve_instrument(&site, &date).await?;
                (r.instrument_id, r.instrument_uuid)
            };
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            t.insert("instrument_id", value(&instrument_id));
            t.insert("instrument_uuid", value(&instrument_uuid));
            if let Some(ft) = &ftype {
                t.insert("ftype", value(ft.to_string()));
            }
            if let Some(deg) = azimuth_offset_deg {
                let mut opts = Table::new();
                opts.insert("azimuth_offset_deg", value(deg));
                t.insert("options", Item::Table(opts));
            }
            if let Some(r) = &description {
                t.insert("description", value(r));
            }
            ("wind", t)
        }
        AddProduct::StareDepol {
            site,
            date,
            description,
        } => {
            validate_date(&date)?;
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            if let Some(r) = &description {
                t.insert("description", value(r));
            }
            ("stare_depol", t)
        }
        AddProduct::Turbulence {
            site,
            date,
            instrument_uuid,
            description,
        } => {
            validate_date(&date)?;
            let (instrument_id, instrument_uuid) = if let Some(uuid) = instrument_uuid {
                let id = resolve_instrument_id(&site, &date, &uuid).await?;
                (id, uuid)
            } else {
                let r = resolve_instrument(&site, &date).await?;
                (r.instrument_id, r.instrument_uuid)
            };
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            t.insert("instrument_id", value(&instrument_id));
            t.insert("instrument_uuid", value(&instrument_uuid));
            if let Some(r) = &description {
                t.insert("description", value(r));
            }
            ("turbulence", t)
        }
        AddProduct::Raw {
            kind,
            site,
            date,
            filename,
            uuid,
            prefix,
            suffix,
            ftype,
            description,
        } => {
            validate_date(&date)?;
            let mut t = Table::new();
            t.insert("id", value(&id));
            t.insert("kind", value(kind.to_string()));
            t.insert("site", value(&site));
            t.insert("date", value(&date));
            if let Some(f) = &filename {
                t.insert("filename", value(f));
            }
            if let Some(u) = &uuid {
                t.insert("uuid", value(u));
            }
            if let Some(p) = &prefix {
                t.insert("prefix", value(p));
            }
            if let Some(s) = &suffix {
                t.insert("suffix", value(s));
            }
            if let Some(ft) = &ftype {
                t.insert("ftype", value(ft.to_string()));
            }
            if let Some(r) = &description {
                t.insert("description", value(r));
            }
            ("raw", t)
        }
    };

    if doc.get(table_name).is_none() {
        doc.insert(table_name, Item::ArrayOfTables(ArrayOfTables::new()));
    }
    let arr = doc[table_name]
        .as_array_of_tables_mut()
        .ok_or_else(|| format!("'{table_name}' is not an array of tables in tests.toml"))?;
    arr.push(table);

    fs::write(&path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))?;

    println!("Added [{id}] to [[{table_name}]] in {}", path.display());
    Ok(())
}

// ── Remove command ──────────────────────────────────────────────────

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

fn cmd_remove(id: &str) -> Result<(), String> {
    let config = read_config()?;
    let entries = config.entries();
    let entry = entries
        .iter()
        .find(|e| e.id() == id)
        .ok_or_else(|| format!("no test found with id '{id}'"))?;

    let product = entry.product();

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

    let config_path = config_path();
    let text = fs::read_to_string(&config_path)
        .map_err(|e| format!("failed to read {}: {e}", config_path.display()))?;
    let mut doc: DocumentMut = text
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", config_path.display()))?;

    remove_from_toml_array(&mut doc, product, id);

    fs::write(&config_path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", config_path.display()))?;

    let lock_path = lock_path();
    if lock_path.exists() {
        let lock_text = fs::read_to_string(&lock_path)
            .map_err(|e| format!("failed to read {}: {e}", lock_path.display()))?;
        let mut lock_doc: DocumentMut = lock_text
            .parse()
            .map_err(|e| format!("failed to parse {}: {e}", lock_path.display()))?;

        remove_from_toml_array(&mut lock_doc, product, id);

        fs::write(&lock_path, lock_doc.to_string())
            .map_err(|e| format!("failed to write {}: {e}", lock_path.display()))?;
    }

    println!("Removed [{id}]");
    Ok(())
}

// ── List command ────────────────────────────────────────────────────

fn cmd_list(
    product_filter: Option<&str>,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
) -> Result<(), String> {
    let config = read_config()?;
    let filtered = filter_entries(
        config.entries(),
        product_filter,
        site_filter,
        id_filter,
        &[],
    );

    if filtered.is_empty() {
        println!("No tests match the given filters.");
        return Ok(());
    }

    println!("{} test(s):\n", filtered.len());
    for entry in &filtered {
        println!("  {entry}");
    }
    Ok(())
}

// ── Check command ───────────────────────────────────────────────────

fn cmd_check() -> Result<(), String> {
    let config = read_config()?;
    let lock = read_lock()?;

    let config_keys: std::collections::HashSet<String> = config
        .entries()
        .iter()
        .map(|e| e.id().to_string())
        .collect();
    let lock_keys = lock.keys();

    let mut ok = true;

    let missing_from_lock: Vec<_> = config_keys.difference(&lock_keys).collect();
    if !missing_from_lock.is_empty() {
        ok = false;
        eprintln!("Tests in tests.toml missing from tests.lock:");
        for k in &missing_from_lock {
            eprintln!("  - {k}");
        }
        eprintln!("\nRun `doptest lock` to generate lock entries for these tests.");
    }

    let extra_in_lock: Vec<_> = lock_keys.difference(&config_keys).collect();
    if !extra_in_lock.is_empty() {
        ok = false;
        eprintln!("Entries in tests.lock not in tests.toml:");
        for k in &extra_in_lock {
            eprintln!("  - {k}");
        }
        eprintln!("\nRemove stale entries or run `doptest lock` to regenerate.");
    }

    if ok {
        println!(
            "OK: tests.toml ({} tests) and tests.lock are consistent.",
            config.test_count()
        );
        Ok(())
    } else {
        Err("check failed".into())
    }
}

// ── Clean command ───────────────────────────────────────────────────

fn cmd_clean() -> Result<(), String> {
    let dir = cache_dir();
    if !dir.exists() {
        println!("Nothing to clean.");
        return Ok(());
    }
    let size = dir_size(&dir);
    fs::remove_dir_all(&dir).map_err(|e| format!("failed to remove {}: {e}", dir.display()))?;
    println!("Removed {} ({})", dir.display(), format_bytes(size));
    Ok(())
}

fn dir_size(path: &Path) -> u64 {
    let mut total = 0;
    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            let meta = entry.metadata();
            if let Ok(m) = meta {
                if m.is_dir() {
                    total += dir_size(&entry.path());
                } else {
                    total += m.len();
                }
            }
        }
    }
    total
}

#[allow(clippy::cast_precision_loss)]
fn format_bytes(bytes: u64) -> String {
    const KIB: u64 = 1024;
    const MIB: u64 = 1024 * KIB;
    const GIB: u64 = 1024 * MIB;
    if bytes >= GIB {
        format!("{:.1} GiB", bytes as f64 / GIB as f64)
    } else if bytes >= MIB {
        format!("{:.1} MiB", bytes as f64 / MIB as f64)
    } else if bytes >= KIB {
        format!("{:.1} KiB", bytes as f64 / KIB as f64)
    } else {
        format!("{bytes} B")
    }
}

// ── Download command ────────────────────────────────────────────────

async fn cmd_download(
    product_filter: Option<&str>,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    force: bool,
) -> Result<(), String> {
    let config = read_config()?;
    let filtered = filter_entries(
        config.entries(),
        product_filter,
        site_filter,
        id_filter,
        &[],
    );

    if filtered.is_empty() {
        println!("No tests match the given filters.");
        return Ok(());
    }

    let api = CloudnetApi::new()?;
    let cache = FileCache::new(&cache_dir());

    println!("Downloading files for {} test(s)...\n", filtered.len());

    let results = download::download_all(&api, &cache, &filtered, force).await;

    let ok_count = results.iter().filter(|(_, r)| r.is_ok()).count();
    let err_count = results.len() - ok_count;

    println!("\nDone: {ok_count} succeeded, {err_count} failed.");

    if err_count > 0 {
        Err("some downloads failed".into())
    } else {
        Ok(())
    }
}

// ── Lock command ────────────────────────────────────────────────────

async fn cmd_lock(
    product_filter: Option<&str>,
    site_filter: Option<&str>,
    id_filter: Option<&str>,
    update_all: bool,
) -> Result<(), String> {
    let config = read_config()?;
    let entries = config.entries();

    if entries.is_empty() {
        println!("No tests in tests.toml.");
        return Ok(());
    }

    let has_filter = product_filter.is_some() || site_filter.is_some() || id_filter.is_some();
    let entry_order: Vec<String> = entries.iter().map(|e| e.id().to_string()).collect();

    let (mut lock, filtered) = if update_all {
        let filtered = filter_entries(entries, product_filter, site_filter, id_filter, &[]);
        (TestsLock::default(), filtered)
    } else if has_filter {
        let lock = read_lock().unwrap_or_default();
        let filtered = filter_entries(entries, product_filter, site_filter, id_filter, &[]);
        (lock, filtered)
    } else {
        let lock = read_lock().unwrap_or_default();
        let lock_keys = lock.keys();
        let filtered: Vec<_> = entries
            .into_iter()
            .filter(|e| !lock_keys.contains(e.id()))
            .collect();
        (lock, filtered)
    };

    if filtered.is_empty() {
        if !has_filter && !update_all {
            println!("All tests already locked. Use --update-all to re-lock everything.");
        } else {
            println!("No tests match filter.");
        }
        return Ok(());
    }

    let _flock = acquire_lock_file()?;

    let api = CloudnetApi::new()?;
    let cache = FileCache::new(&cache_dir());

    lock.meta.locked_at = chrono::Utc::now().to_rfc3339();
    lock.meta.doppy_version = doppy_version();

    if update_all {
        write_lock(&lock)?;
    }

    let total = filtered.len();

    for (i, entry) in filtered.iter().enumerate() {
        let n = i + 1;
        let result = async {
            let resolved = download::resolve_and_download(&api, &cache, entry, false).await?;
            let local_records = download::build_local_records(&cache, &resolved.records)?;
            python::run_lock_helper(entry, &local_records).await
        }
        .await;

        match &result {
            Ok(_) => println!("[{n}/{total}] Locking {entry} ... \x1b[32mOK\x1b[0m"),
            Err(e) => {
                println!("[{n}/{total}] Locking {entry} ... \x1b[31mERROR\x1b[0m");
                eprintln!("  {e}");
            }
        }

        if let Ok(r) = result {
            lock.insert(entry, r.input, r.expect);
            write_lock(&lock)?;
        }
    }

    let order_refs: Vec<&str> = entry_order.iter().map(String::as_str).collect();
    lock.sort_by_ids(&order_refs);
    write_lock(&lock)?;

    println!("\nWrote {}", lock_path().display());
    Ok(())
}

// ── Run command ─────────────────────────────────────────────────────

async fn cmd_run(
    site_filter: Option<&str>,
    product_filter: Option<&str>,
    id_filter: Option<&str>,
    exclude_sites: &[String],
) -> Result<(), String> {
    let config = read_config()?;
    let lock = read_lock()?;
    let filtered = filter_entries(
        config.entries(),
        product_filter,
        site_filter,
        id_filter,
        exclude_sites,
    );

    if filtered.is_empty() {
        println!("No tests match the given filters.");
        return Ok(());
    }

    let api = CloudnetApi::new()?;
    let cache = FileCache::new(&cache_dir());

    println!("Running {} test(s)...\n", filtered.len());

    let mut passed = 0u32;
    let mut failed = 0u32;
    let mut errors = 0u32;

    let total = filtered.len();

    for (i, entry) in filtered.iter().enumerate() {
        let n = i + 1;

        let Some(expect) = lock.find_expect(entry) else {
            errors += 1;
            println!(
                "[{n}/{total}] \x1b[31mERROR\x1b[0m {entry} — no lock entry (run `doptest lock`)"
            );
            continue;
        };

        let outcome = async {
            let resolved = download::resolve_and_download(&api, &cache, entry, false).await?;
            let local_records = download::build_local_records(&cache, &resolved.records)?;
            let result = python::run_lock_helper(entry, &local_records).await?;
            let diffs = compare::compare_values(expect, &result.expect, "expect");
            Ok::<_, String>(diffs)
        }
        .await;

        match outcome {
            Ok(diffs) if diffs.is_empty() => {
                passed += 1;
                println!("[{n}/{total}] \x1b[32mPASS\x1b[0m {entry}");
            }
            Ok(diffs) => {
                failed += 1;
                println!("[{n}/{total}] \x1b[31mFAIL\x1b[0m {entry}");
                for diff in &diffs {
                    println!("         {diff}");
                }
            }
            Err(e) => {
                errors += 1;
                println!("[{n}/{total}] \x1b[31mERROR\x1b[0m {entry} — {e}");
            }
        }
    }

    println!("\n{}", "=".repeat(60));
    println!("Results: {passed} passed, {failed} failed, {errors} errors / {total} total");

    if failed + errors > 0 {
        println!("\x1b[31mFAILED\x1b[0m");
        Err("some tests failed".into())
    } else {
        println!("\x1b[32mALL PASSED\x1b[0m");
        Ok(())
    }
}

// ── Validation ──────────────────────────────────────────────────────

fn validate_date(date: &str) -> Result<(), String> {
    chrono::NaiveDate::parse_from_str(date, "%Y-%m-%d")
        .map_err(|_| format!("invalid date '{date}', expected YYYY-MM-DD format"))?;
    Ok(())
}

// ── Main ────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Command::Add { product } => cmd_add(product).await,
        Command::Remove { id } => cmd_remove(&id),
        Command::List { product, site, id } => {
            cmd_list(product.as_deref(), site.as_deref(), id.as_deref())
        }
        Command::Check => cmd_check(),
        Command::Clean => cmd_clean(),
        Command::Download {
            product,
            site,
            id,
            force,
        } => cmd_download(product.as_deref(), site.as_deref(), id.as_deref(), force).await,
        Command::Lock {
            product,
            site,
            id,
            update_all,
        } => {
            cmd_lock(
                product.as_deref(),
                site.as_deref(),
                id.as_deref(),
                update_all,
            )
            .await
        }
        Command::Sample { action } => cmd_sample(action).await,
        Command::Run {
            site,
            product,
            kind,
            exclude_site,
            id,
        } => {
            let product_filter = product.as_deref().or(kind.as_deref());
            cmd_run(
                site.as_deref(),
                product_filter,
                id.as_deref(),
                &exclude_site,
            )
            .await
        }
        Command::Legacy { action } => cmd_legacy(action).await,
    };

    if let Err(e) = result {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

async fn cmd_sample(action: SampleAction) -> Result<(), String> {
    match action {
        SampleAction::Fetch { force } => sample::cmd_sample_fetch(force).await,
        SampleAction::Stare {
            n,
            force,
            per_cluster,
            add,
        } => sample::cmd_sample_stare(n, force, per_cluster, add).await,
        SampleAction::Wind {
            n,
            force,
            per_cluster,
            add,
        } => sample::cmd_sample_wind(n, force, per_cluster, add).await,
        SampleAction::Turbulence {
            n,
            force,
            per_cluster,
            add,
        } => sample::cmd_sample_turbulence(n, force, per_cluster, add).await,
    }
}

async fn cmd_legacy(action: LegacyAction) -> Result<(), String> {
    match action {
        LegacyAction::Run {
            category,
            product,
            site,
            source,
            id,
            include_slow,
        } => {
            legacy::cmd_legacy_run(
                category.as_deref(),
                product.as_deref(),
                site.as_deref(),
                source.as_deref(),
                id.as_deref(),
                include_slow,
            )
            .await
        }
        LegacyAction::List {
            category,
            product,
            site,
            source,
            id,
            include_slow,
        } => legacy::cmd_legacy_list(
            category.as_deref(),
            product.as_deref(),
            site.as_deref(),
            source.as_deref(),
            id.as_deref(),
            include_slow,
        ),
    }
}

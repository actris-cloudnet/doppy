use std::io::Read;

use futures::stream::{self, StreamExt};

use crate::api::{CloudnetApi, RawRecord};
use crate::cache::FileCache;
use crate::types::{RawKind, TestEntry};

const CONCURRENT_DOWNLOADS: usize = 8;

pub struct ResolvedTest {
    pub records: Vec<RawRecord>,
}

pub async fn resolve_and_download(
    api: &CloudnetApi,
    cache: &FileCache,
    entry: &TestEntry,
    force: bool,
) -> Result<ResolvedTest, String> {
    let records = fetch_records(api, cache, entry, force).await?;
    download_files(api, cache, &records, force).await?;
    Ok(ResolvedTest { records })
}

async fn fetch_records(
    api: &CloudnetApi,
    cache: &FileCache,
    entry: &TestEntry,
    force: bool,
) -> Result<Vec<RawRecord>, String> {
    if !force && let Some(cached) = cache.load_records(entry.id()) {
        return Ok(cached);
    }

    let records = query_api(api, entry).await?;
    cache.store_records(entry.id(), &records)?;
    Ok(records)
}

async fn query_api(api: &CloudnetApi, entry: &TestEntry) -> Result<Vec<RawRecord>, String> {
    match entry {
        TestEntry::Stare {
            site,
            date,
            instrument_uuid,
            ..
        }
        | TestEntry::Wind {
            site,
            date,
            instrument_uuid,
            ..
        } => {
            api.get_records_by_instrument_uuid(site, instrument_uuid, date)
                .await
        }
        TestEntry::StareDepol { site, date, .. } | TestEntry::Turbulence { site, date, .. } => {
            api.get_raw_records(site, date).await
        }
        TestEntry::Raw {
            site,
            date,
            kind,
            filename,
            ..
        } => {
            if *kind == RawKind::HaloSysParams {
                let mut params = vec![
                    ("site", site.as_str()),
                    ("instrument", "halo-doppler-lidar"),
                    ("date", date.as_str()),
                ];
                if let Some(f) = filename {
                    params.push(("filename", f.as_str()));
                }
                api.get_raw_files(&params).await
            } else {
                api.get_raw_records(site, date).await
            }
        }
    }
}

async fn download_files(
    api: &CloudnetApi,
    cache: &FileCache,
    records: &[RawRecord],
    force: bool,
) -> Result<(), String> {
    let to_download: Vec<&RawRecord> = records
        .iter()
        .filter(|r| force || !cache.has_file(&r.uuid))
        .collect();

    if to_download.is_empty() {
        return Ok(());
    }

    let results: Vec<Result<(), String>> = stream::iter(to_download)
        .map(|rec| async {
            let bytes = api.download_bytes(&rec.download_url).await?;
            let content = decompress_if_gz(&rec.filename, bytes)?;
            cache.store_file(&rec.uuid, &content)
        })
        .buffer_unordered(CONCURRENT_DOWNLOADS)
        .collect()
        .await;

    for result in results {
        result?;
    }

    Ok(())
}

fn decompress_if_gz(filename: &str, data: Vec<u8>) -> Result<Vec<u8>, String> {
    if std::path::Path::new(filename)
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

pub async fn download_all(
    api: &CloudnetApi,
    cache: &FileCache,
    entries: &[TestEntry],
    force: bool,
) -> Vec<(usize, Result<ResolvedTest, String>)> {
    let total = entries.len();
    let mut results = Vec::with_capacity(total);

    for (i, entry) in entries.iter().enumerate() {
        eprint!("[{}/{}] {} ... ", i + 1, total, entry);
        let result = resolve_and_download(api, cache, entry, force).await;
        match &result {
            Ok(resolved) => {
                let cached_count = resolved
                    .records
                    .iter()
                    .filter(|r| cache.has_file(&r.uuid))
                    .count();
                eprintln!("\x1b[32m{cached_count} file(s)\x1b[0m");
            }
            Err(e) => {
                eprintln!("\x1b[31mERROR\x1b[0m: {e}");
            }
        }
        results.push((i, result));
    }

    results
}

pub fn build_local_records(
    cache: &FileCache,
    records: &[RawRecord],
) -> Result<Vec<serde_json::Value>, String> {
    let abs_root = cache_abs_root(cache)?;
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

fn cache_abs_root(cache: &FileCache) -> Result<std::path::PathBuf, String> {
    let root = cache.root();
    if root.is_absolute() {
        Ok(root.to_path_buf())
    } else {
        std::env::current_dir()
            .map_err(|e| format!("failed to get cwd: {e}"))?
            .join(root)
            .canonicalize()
            .map_err(|e| format!("failed to canonicalize cache path: {e}"))
    }
}

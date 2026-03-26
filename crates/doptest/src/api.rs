use std::time::Duration;

use reqwest::Client;
use serde::{Deserialize, Serialize};

pub const BASE_URL: &str = "https://cloudnet.fmi.fi/api";
const TIMEOUT_SECS: u64 = 1800;
const MAX_RETRIES: u32 = 10;
const BACKOFF_FACTOR: f64 = 0.2;

const INSTRUMENTS: &[&str] = &[
    "halo-doppler-lidar",
    "wls100s",
    "wls200s",
    "wls400s",
    "wls70",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RawRecord {
    pub filename: String,
    pub uuid: String,
    pub download_url: String,
    pub instrument: Instrument,
    #[serde(default)]
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Instrument {
    pub uuid: String,
    pub instrument_id: String,
}

pub struct CloudnetApi {
    client: Client,
}

impl CloudnetApi {
    pub fn new() -> Result<Self, String> {
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

    pub async fn get_json<T: serde::de::DeserializeOwned>(&self, url: &str) -> Result<T, String> {
        let resp = self.get_with_retry(url).await?;
        resp.json()
            .await
            .map_err(|e| format!("failed to parse response: {e}"))
    }

    pub async fn get_raw_files(&self, params: &[(&str, &str)]) -> Result<Vec<RawRecord>, String> {
        let url = reqwest::Url::parse_with_params(&format!("{BASE_URL}/raw-files"), params)
            .map_err(|e| format!("invalid URL params: {e}"))?;
        let resp = self.get_with_retry(url.as_str()).await?;
        resp.json()
            .await
            .map_err(|e| format!("failed to parse API response: {e}"))
    }

    /// Get raw records filtered by the standard set of instrument types.
    pub async fn get_raw_records(&self, site: &str, date: &str) -> Result<Vec<RawRecord>, String> {
        let mut params: Vec<(&str, &str)> = Vec::new();
        for instr in INSTRUMENTS {
            params.push(("instrument", instr));
        }
        params.push(("site", site));
        params.push(("date", date));
        self.get_raw_files(&params).await
    }

    /// Get raw records for a specific instrument UUID (queries all raw files for
    /// site/date, then filters client-side).
    pub async fn get_records_by_instrument_uuid(
        &self,
        site: &str,
        instrument_uuid: &str,
        date: &str,
    ) -> Result<Vec<RawRecord>, String> {
        let records = self
            .get_raw_files(&[("site", site), ("date", date)])
            .await?;
        Ok(records
            .into_iter()
            .filter(|r| r.instrument.uuid == instrument_uuid)
            .collect())
    }

    /// Download raw bytes from a URL (with retry).
    pub async fn download_bytes(&self, url: &str) -> Result<Vec<u8>, String> {
        let resp = self.get_with_retry(url).await?;
        let bytes = resp
            .bytes()
            .await
            .map_err(|e| format!("failed to read response body: {e}"))?;
        Ok(bytes.into())
    }
}

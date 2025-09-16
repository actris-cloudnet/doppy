use chrono::{DateTime, NaiveDate, Utc};
use regex::Regex;
use serde::{Deserialize, Deserializer};
use uuid::Uuid;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InstrumentUploadResponse {
    pub uuid: Uuid,
    pub checksum: String,
    pub filename: String,
    pub measurement_date: NaiveDate,

    #[serde(deserialize_with = "deserialize_string_to_u64")]
    pub size: u64,

    pub status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub tags: Vec<String>,
    pub site: SiteInfo,
    pub instrument: InstrumentInfo,
    pub download_url: String,
}

fn deserialize_string_to_u64<'de, D>(deserializer: D) -> Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    s.parse::<u64>().map_err(serde::de::Error::custom)
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SiteInfo {
    pub id: String,
    pub human_readable_name: String,
    pub station_name: String,

    #[serde(default)]
    pub r#type: Vec<String>,

    pub latitude: f64,
    pub longitude: f64,
    pub altitude: i32,
    pub gaw: Option<String>,
    pub dvas_id: Option<String>,
    pub actris_id: Option<i16>,
    pub country: Option<String>,
    pub country_code: Option<String>,
    pub country_subdivision_code: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InstrumentInfo {
    pub uuid: Uuid,
    pub pid: String,
    pub name: String,
    pub owners: Vec<String>,
    pub model: String,
    pub r#type: String,
    pub serial_number: Option<String>,
    pub instrument_id: Option<String>,
    #[serde(rename = "_type")]
    pub _type: Option<String>,
}

pub fn get_metadata(filename: &str, uuid: &Uuid) -> InstrumentUploadResponse {
    let url = format!("https://cloudnet.fmi.fi/api/raw-files?filename={filename}");
    let iu = reqwest::blocking::get(url)
        .unwrap()
        .json::<Vec<InstrumentUploadResponse>>()
        .unwrap();
    let iu = iu.into_iter().find(|iu| iu.uuid == *uuid);
    let iu = iu
        .unwrap_or_else(|| panic!("Cannot find filename '{filename}' with matching uuid '{uuid}'"));
    iu
}

pub fn get_metadata_for_day(
    site_id: &str,
    measurement_date: &NaiveDate,
    instrument_uuid: &Uuid,
    include_filename_re: Option<&str>,
    exclude_filename_re: Option<&str>,
) -> Vec<InstrumentUploadResponse> {
    let url =
        format!("https://cloudnet.fmi.fi/api/raw-files?site={site_id}&date={measurement_date}");
    let ius = reqwest::blocking::get(url)
        .unwrap()
        .json::<Vec<InstrumentUploadResponse>>()
        .unwrap();
    let mut ius: Vec<_> = ius
        .into_iter()
        .filter(|iu| iu.instrument.uuid == *instrument_uuid)
        .collect();
    if let Some(re) = include_filename_re {
        let re = Regex::new(re).unwrap();
        ius.retain(|u| re.is_match(&u.filename));
    }
    if let Some(re) = exclude_filename_re {
        let re = Regex::new(re).unwrap();
        ius.retain(|u| !re.is_match(&u.filename));
    }
    ius
}

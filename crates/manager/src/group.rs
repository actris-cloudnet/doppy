use csv::Reader;
use once_cell::sync::Lazy;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, fs::File};

type FileTypeMap = HashMap<FileType, Vec<RawRecord>>;

#[allow(dead_code)]
#[derive(Debug, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct RawRecord {
    pub uuid: String,
    pub checksum: String,
    pub filename: String,
    pub measurement_date: String,
    pub size: String,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
    pub site_id: String,
    pub instrument_id: String,
    pub instrument_pid: String,
    pub tags: String,
    pub s3key: String,
    pub instrument_info_uuid: String,
}

#[derive(Serialize, Deserialize, Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub enum HaloFileType {
    Stare,
    Vad,
    Rhi,
    WindProfile,
    ProcessedWindProfile,
    Background,
    SystemParameters,
    TimeSync,
    User1,
    User2,
    User3,
    User4,
    User5,
}
#[derive(Serialize, Deserialize, Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub enum WindCube200FileType {
    Dbs,
    Fixed,
    Ppi,
    Vad,
    Rhi,
    Volume,
    SpectrumDbs,
    SpectrumPpi,
    SpectrumFixed,
    SpectrumVad,
    SpectrumRhi,
    SpectrumVolume,
    Environmental,
}

#[derive(Serialize, Deserialize, Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub enum WindCube70FileType {
    WindLz1R10s,
    WindLz1Lb87R10s,
}

#[derive(Serialize, Deserialize, Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub enum FileType {
    Halo(HaloFileType),
    WindCube200(WindCube200FileType),
    WindCube70(WindCube70FileType),
}

#[derive(Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub struct InstrumentGroup {
    pub site: String,
    pub pid: String,
    pub uuid: String,
}

pub fn group() -> HashMap<InstrumentGroup, FileTypeMap> {
    let file = File::open("records.csv").unwrap();
    let mut rdr = Reader::from_reader(file);

    let mut groups: HashMap<InstrumentGroup, FileTypeMap> = HashMap::new();

    for row in rdr.deserialize::<RawRecord>() {
        let row = row.unwrap();
        groups
            .entry(InstrumentGroup {
                site: row.site_id.clone(),
                pid: row.instrument_pid.clone(),
                uuid: row.instrument_info_uuid.clone(),
            })
            .or_default()
            .entry(filetype_from_record(&row))
            .or_default()
            .push(row.clone())
    }
    groups
}

fn filetype_from_record(record: &RawRecord) -> FileType {
    match record.instrument_id.as_str() {
        "halo-doppler-lidar" => filetype_from_halo(&record.filename),
        "wls200s" => filetype_from_wls200s(&record.filename),
        "wls70" => filetype_from_wls70(&record.filename),
        val => todo!("Instrument id {val} not implemented yet"),
    }
}

static PREFIX_MAP: Lazy<HashMap<&'static str, HaloFileType>> = Lazy::new(|| {
    use HaloFileType as H;

    HashMap::from([
        ("Background", H::Background),
        ("Stare", H::Stare),
        ("VAD", H::Vad),
        ("RHI", H::Rhi),
        ("Wind_Profile", H::WindProfile),
        ("Processed_Wind_Profile", H::ProcessedWindProfile),
        ("system_parameters", H::SystemParameters),
        ("Time_Sync", H::TimeSync),
        ("User1", H::User1),
        ("User2", H::User2),
        ("User3", H::User3),
        ("User4", H::User4),
        ("User5", H::User5),
    ])
});

fn filetype_from_halo(filename: &str) -> FileType {
    PREFIX_MAP
        .iter()
        .find_map(|(prefix, file_type)| {
            filename
                .strip_prefix(prefix)
                .map(|_| FileType::Halo(file_type.clone()))
        })
        .unwrap_or_else(|| panic!("Unknown filename pattern: {}", filename))
}

static WLS200_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^WLS[0-9a-zA-Z]*-\d+_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_([a-zA-Z0-9]+)_.*")
        .unwrap()
});

static WLS200_PATTERN_SPECTRUM: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"^WLS[0-9a-zA-Z]*-\d+_Spectrum_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_([a-zA-Z0-9]+)_.*",
    )
    .unwrap()
});

static WLS200_PATTERN_ENVIRONMENTAL: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^WLS[0-9a-zA-Z]*-\d+_environmental_data_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.*")
        .unwrap()
});

static WLS200_MAP: Lazy<HashMap<&'static str, WindCube200FileType>> = Lazy::new(|| {
    use WindCube200FileType as W;
    HashMap::from([
        ("dbs", W::Dbs),
        ("fixed", W::Fixed),
        ("ppi", W::Ppi),
        ("vad", W::Vad),
        ("rhi", W::Rhi),
        ("volume", W::Volume),
    ])
});

// Mapping for spectrum file types
static WLS200_SPECTRUM_MAP: Lazy<HashMap<&'static str, WindCube200FileType>> = Lazy::new(|| {
    use WindCube200FileType as W;
    HashMap::from([
        ("DBS", W::SpectrumDbs),
        ("PPI", W::SpectrumPpi),
        ("FIXED", W::SpectrumFixed),
        ("VAD", W::SpectrumVad),
        ("RHI", W::SpectrumRhi),
        ("VOLUME", W::SpectrumVolume),
    ])
});

fn filetype_from_wls200s(filename: &str) -> FileType {
    if let Some(cap) = WLS200_PATTERN.captures(filename) {
        if let Some(file_type) = cap
            .get(1)
            .map(|m| m.as_str())
            .and_then(|f| WLS200_MAP.get(f))
        {
            return FileType::WindCube200(file_type.clone());
        }
    }

    if let Some(cap) = WLS200_PATTERN_SPECTRUM.captures(filename) {
        if let Some(file_type) = cap
            .get(1)
            .map(|m| m.as_str())
            .and_then(|f| WLS200_SPECTRUM_MAP.get(f))
        {
            return FileType::WindCube200(file_type.clone());
        }
    }

    if WLS200_PATTERN_ENVIRONMENTAL.is_match(filename) {
        return FileType::WindCube200(WindCube200FileType::Environmental);
    }

    panic!("Invalid filename format: {}", filename)
}

static WLS70_PATTERN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^wlscerea_0a_(.*)-HR_v01_\d{8}_\d{6}.rtd").unwrap());

static WLS70_MAP: Lazy<HashMap<&'static str, WindCube70FileType>> = Lazy::new(|| {
    use WindCube70FileType::*;
    HashMap::from([
        ("windLz1R10s", WindLz1R10s),
        ("windLz1Lb87R10s", WindLz1Lb87R10s),
    ])
});

fn filetype_from_wls70(filename: &str) -> FileType {
    if let Some(cap) = WLS70_PATTERN.captures(filename) {
        if let Some(file_type) = cap
            .get(1)
            .map(|m| m.as_str())
            .and_then(|f| WLS70_MAP.get(f))
        {
            return FileType::WindCube70(file_type.clone());
        }
    }

    panic!("Invalid filename format: {}", filename)
}

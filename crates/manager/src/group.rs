use csv::Reader;
use once_cell::sync::Lazy;
use regex::Regex;
use serde::Deserialize;
use std::{collections::HashMap, fs::File};

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

#[derive(Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
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
#[derive(Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
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

#[derive(Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
pub enum WindCube70FileType {
    WindLz1R10s,
    WindLz1Lb87R10s,
}

#[derive(Hash, Eq, PartialEq, PartialOrd, Ord, Clone, Debug)]
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

pub fn group() -> HashMap<InstrumentGroup, HashMap<FileType, Vec<RawRecord>>> {
    let file = File::open("records.csv").unwrap();
    let mut rdr = Reader::from_reader(file);

    let mut groups: HashMap<InstrumentGroup, HashMap<FileType, Vec<RawRecord>>> = HashMap::new();

    for row in rdr.deserialize::<RawRecord>().take(100000000) {
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
    use HaloFileType::*;

    HashMap::from([
        ("Background", Background),
        ("Stare", Stare),
        ("VAD", Vad),
        ("RHI", Rhi),
        ("Wind_Profile", WindProfile),
        ("Processed_Wind_Profile", ProcessedWindProfile),
        ("system_parameters", SystemParameters),
        ("Time_Sync", TimeSync),
        ("User1", User1),
        ("User2", User2),
        ("User3", User3),
        ("User4", User4),
        ("User5", User5),
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
    use WindCube200FileType::*;
    HashMap::from([
        ("dbs", Dbs),
        ("fixed", Fixed),
        ("ppi", Ppi),
        ("vad", Vad),
        ("rhi", Rhi),
        ("volume", Volume),
    ])
});

// Mapping for spectrum file types
static WLS200_SPECTRUM_MAP: Lazy<HashMap<&'static str, WindCube200FileType>> = Lazy::new(|| {
    use WindCube200FileType::*;
    HashMap::from([
        ("DBS", SpectrumDbs),
        ("PPI", SpectrumPpi),
        ("FIXED", SpectrumFixed),
        ("VAD", SpectrumVad),
        ("RHI", SpectrumRhi),
        ("VOLUME", SpectrumVolume),
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

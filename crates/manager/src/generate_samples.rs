use csv::Reader;
use regex::Regex;
use serde::Deserialize;
use std::{collections::HashSet, fs::File};

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RawRecord {
    uuid: String,
    checksum: String,
    filename: String,
    measurement_date: String,
    size: String,
    status: String,
    created_at: String,
    updated_at: String,
    site_id: String,
    instrument_id: String,
    instrument_pid: String,
    tags: String,
    s3key: String,
    instrument_info_uuid: String,
}

#[derive(Hash, Eq, PartialEq)]
enum HaloFileType {
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
#[derive(Hash, Eq, PartialEq)]
enum WindCubeFileType {
    Dbs,
    Fixed,
    Ppi,
    Vad,
    SpectrumDbs,
    SpectrumPpi,
    SpectrumFixed,
    Other,
}

#[derive(Hash, Eq, PartialEq)]
enum FileType {
    Halo(HaloFileType),
    WindCube(WindCubeFileType),
}

pub fn sample() {
    let file = File::open("records.csv").unwrap();
    let mut rdr = Reader::from_reader(file);

    let mut file_groups = HashSet::new();

    for row in rdr.deserialize::<RawRecord>().take(400000) {
        let row = row.unwrap();
        file_groups.insert(filetype_from_record(&row));
    }
}

fn filetype_from_record(record: &RawRecord) -> FileType {
    match record.instrument_id.as_str() {
        "halo-doppler-lidar" => filetype_from_halo(&record.filename),
        "wls200s" => filetype_from_wls200s(&record.filename),
        "wls70" => filetype_from_wls70(&record.filename),
        val => todo!("Instrument id {val} not implemented yet"),
    }
}

fn filetype_from_halo(filename: &str) -> FileType {
    if filename.starts_with("Background") {
        FileType::Halo(HaloFileType::Background)
    } else if filename.starts_with("Stare") {
        FileType::Halo(HaloFileType::Stare)
    } else if filename.starts_with("VAD") {
        FileType::Halo(HaloFileType::Vad)
    } else if filename.starts_with("RHI") {
        FileType::Halo(HaloFileType::Rhi)
    } else if filename.starts_with("Wind_Profile") {
        FileType::Halo(HaloFileType::WindProfile)
    } else if filename.starts_with("Processed_Wind_Profile") {
        FileType::Halo(HaloFileType::ProcessedWindProfile)
    } else if filename.starts_with("system_parameters") {
        FileType::Halo(HaloFileType::SystemParameters)
    } else if filename.starts_with("Time_Sync") {
        FileType::Halo(HaloFileType::TimeSync)
    } else if filename.starts_with("User1") {
        FileType::Halo(HaloFileType::User1)
    } else if filename.starts_with("User2") {
        FileType::Halo(HaloFileType::User2)
    } else if filename.starts_with("User3") {
        FileType::Halo(HaloFileType::User3)
    } else if filename.starts_with("User4") {
        FileType::Halo(HaloFileType::User4)
    } else if filename.starts_with("User5") {
        FileType::Halo(HaloFileType::User5)
    } else {
        todo!("{filename}")
    }
}

fn filetype_from_wls200s(filename: &str) -> FileType {
    let pattern =
        Regex::new(r"^WLS[0-9a-zA-Z]*-\d+_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_([a-zA-Z0-9]+)_.*")
            .unwrap();

    let pattern_spectrum = Regex::new(
        r"^WLS[0-9a-zA-Z]*-\d+_Spectrum_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_([a-zA-Z0-9]+)_.*",
    )
    .unwrap();

    let pattern_environmental = Regex::new(
        r"^WLS[0-9a-zA-Z]*-\d+_environmental_data_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.*",
    )
    .unwrap();

    println!("{filename}");

    match pattern
        .captures(filename)
        .and_then(|cap| cap.get(1).map(|m| m.as_str()))
    {
        Some("dbs") => FileType::WindCube(WindCubeFileType::Dbs),
        Some("fixed") => FileType::WindCube(WindCubeFileType::Fixed),
        Some("ppi") => FileType::WindCube(WindCubeFileType::Ppi),
        Some("vad") => FileType::WindCube(WindCubeFileType::Vad),
        Some(val) => todo!("Handle unexpected file type: {val}"),
        None => {
            match pattern_spectrum
                .captures(filename)
                .and_then(|cap| cap.get(1).map(|m| m.as_str()))
            {
                Some("DBS") => FileType::WindCube(WindCubeFileType::SpectrumDbs),
                Some("PPI") => FileType::WindCube(WindCubeFileType::SpectrumPpi),
                Some("FIXED") => FileType::WindCube(WindCubeFileType::SpectrumFixed),
                Some(val) => todo!("Handle unexpected spectrum match {val}"),
                None => todo!("Invalid filename format: {filename}"),
            }
        }
    }
}

fn filetype_from_wls70(filename: &str) -> FileType {
    FileType::WindCube(WindCubeFileType::Other)
}

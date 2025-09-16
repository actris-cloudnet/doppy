use clap::ValueEnum;
use std::{
    fs::File,
    io::{Read, Write},
    path::{Path, PathBuf},
    process::Command,
};

use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::raw_files::InstrumentUploadResponse;

#[derive(Debug, Ord, Eq, PartialEq, PartialOrd, Clone, Serialize, Deserialize, ValueEnum)]
pub enum TestType {
    Raw,
    Stare,
    Wind,
}

#[derive(Debug, Ord, Eq, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Testcase {
    pub r#type: TestType,
    pub description: Option<String>,
    pub files: Vec<Testfile>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct Tests {
    #[serde(rename = "testcase")]
    pub testcases: Vec<Testcase>,
}

#[derive(Debug, Ord, Eq, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Testfile {
    pub site_id: String,
    pub filename: String,
    pub measurement_date: NaiveDate,
    pub instrument_id: String,
    pub uuid: Uuid,
    pub checksum: String,
    pub instrument_uuid: Uuid,
    pub download_url: String,
}

impl From<&InstrumentUploadResponse> for Testfile {
    fn from(iu: &InstrumentUploadResponse) -> Self {
        Testfile {
            uuid: iu.uuid,
            checksum: iu.checksum.clone(),
            filename: iu.filename.clone(),
            measurement_date: iu.measurement_date,
            site_id: iu.site.id.clone(),
            instrument_uuid: iu.instrument.uuid,
            instrument_id: iu.instrument.instrument_id.clone().unwrap(),
            download_url: iu.download_url.clone(),
        }
    }
}

pub fn get_testfile_path() -> PathBuf {
    find_project_root().join("tests").join("tests.toml")
}
pub fn get_tests() -> Result<Tests, String> {
    let testfilepath = get_testfile_path();
    let mut f = File::open(&testfilepath).map_err(|err| format!("{err}"))?;
    let mut buf = String::new();
    f.read_to_string(&mut buf).unwrap();
    let tests: Tests = toml::from_str(&buf).unwrap();
    Ok(tests)
}

pub fn add_testcase_from_instrument_uploads(
    r#type: &TestType,
    description: Option<&str>,
    uploads: &[InstrumentUploadResponse],
) {
    // Read the old cases
    let testfilepath = get_testfile_path();

    let mut tests: Tests = if let Ok(mut f) = File::open(&testfilepath) {
        let mut buf = String::new();
        f.read_to_string(&mut buf).unwrap();
        toml::from_str(&buf).unwrap()
    } else {
        Tests::default()
    };

    // Add new testcase
    let testfiles = uploads.iter().map(Testfile::from).collect();
    let testcase = Testcase {
        r#type: r#type.clone(),
        description: description.map(str::to_string),
        files: testfiles,
    };
    tests.testcases.push(testcase);
    tests.testcases.sort();
    tests.testcases.dedup();
    tests.testcases.iter_mut().for_each(|t| t.files.sort());

    let tests = toml::to_string(&tests).unwrap();

    let mut f = File::create(testfilepath).unwrap();
    f.write_all(tests.as_bytes()).unwrap();
}

pub fn find_project_root() -> PathBuf {
    let out = Command::new("git")
        .args(["rev-parse", "--show-toplevel"])
        .output()
        .unwrap();
    if out.status.success() {
        let root = String::from_utf8(out.stdout).unwrap();
        let root = root.trim();
        return Path::new(root).to_owned();
    }
    panic!("Failed to get project root")
}

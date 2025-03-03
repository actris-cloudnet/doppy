use serde::{Deserialize, Serialize};
use serde_json;
use std::{collections::HashMap, fs::File};

use crate::group;

#[derive(Serialize, Deserialize, Eq, Hash, PartialEq, Ord, PartialOrd, Debug)]
struct TestGroup {
    site: String,
    instrument_pid: String,
    filetype: group::FileType,
}

#[allow(dead_code)]
#[derive(Serialize, Deserialize, Ord, PartialEq, PartialOrd, Eq, Debug)]
struct RawTestFile {
    uuid: String,
    checksum: String,
    filename: String,
    measurement_date: String,
}

pub fn generate_raw_tests() {
    let groups = group::group();
    let mut test_groups: HashMap<TestGroup, Vec<RawTestFile>> = HashMap::new();
    for (g, ftg) in groups {
        for (ft, records) in ftg {
            for r in records.iter().take(10) {
                test_groups
                    .entry(TestGroup {
                        site: g.site.clone(),
                        instrument_pid: g.pid.clone(),
                        filetype: ft.clone(),
                    })
                    .or_default()
                    .push(RawTestFile {
                        uuid: r.uuid.clone(),
                        checksum: r.checksum.clone(),
                        filename: r.filename.clone(),
                        measurement_date: r.measurement_date.clone(),
                    });
            }
        }
    }
    for files in test_groups.values_mut() {
        files.sort_by_key(|f| (f.measurement_date.clone(), f.filename.clone()));
    }
    let mut test_groups: Vec<(_, _)> = test_groups.into_iter().collect();
    test_groups.sort();

    let file = File::create("tests/test-samples-raw.json").unwrap();
    serde_json::to_writer_pretty(file, &test_groups).unwrap();
}

use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use reqwest::{self, Client};
use serde::{Deserialize, Serialize};
use serde_json;
use std::sync::Arc;
use std::thread::sleep;
use std::time::Duration;
use std::{
    collections::HashMap,
    fs::{self, File},
    io::{BufReader, Write},
    path::PathBuf,
};
use tokio::sync::Semaphore;

use crate::group;

#[derive(Serialize, Deserialize, Eq, Hash, PartialEq, Ord, PartialOrd, Debug, Clone)]
struct TestGroup {
    site: String,
    instrument_pid: String,
    filetype: group::FileType,
}

#[allow(dead_code)]
#[derive(Serialize, Deserialize, Ord, PartialEq, PartialOrd, Eq, Debug, Clone)]
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
            for r in records.iter().filter(|r| r.status != "invalid").take(10) {
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

pub async fn download_raw_tests() {
    let file = File::open("tests/test-samples-raw.json").unwrap();
    let reader = BufReader::new(file);
    let test_groups: Vec<(TestGroup, Vec<RawTestFile>)> = serde_json::from_reader(reader).unwrap();

    let n = test_groups
        .iter()
        .map(|(_, files)| files.len())
        .sum::<usize>();
    let semaphore = Arc::new(Semaphore::new(8));
    let mut tasks = Vec::new();
    let client = Arc::new(
        Client::builder()
            .timeout(std::time::Duration::from_secs(2400))
            .build()
            .unwrap(),
    );
    let multi_pb = Arc::new(MultiProgress::new());

    let global_pb = multi_pb.add(ProgressBar::new(n as u64));
    global_pb.set_style(
        ProgressStyle::default_bar()
            .template("[{elapsed_precise} | eta: {eta:5}] {bar:40.cyan/blue} {pos:>7}/{len:7}")
            .unwrap()
            .progress_chars("##-"),
    );
    global_pb.enable_steady_tick(Duration::from_millis(100));

    for (g, files) in &test_groups {
        for f in files {
            let g = g.clone();
            let f = f.clone();
            let sem = semaphore.clone();
            let client = Arc::clone(&client);
            let multi_pb = Arc::clone(&multi_pb);
            let global_pb = global_pb.clone();

            tasks.push(tokio::spawn(async move {
                let _permit = sem.acquire().await.unwrap();

                let pb = multi_pb.add(ProgressBar::new_spinner());
                pb.set_style(
                    ProgressStyle::default_spinner()
                        .template("{spinner:.green} {msg}")
                        .unwrap(),
                );
                pb.enable_steady_tick(std::time::Duration::from_millis(100));
                pb.set_message(format!("{} Downloading", f.filename));

                download_raw_test_file(&client, &g, &f).await;
                pb.finish_and_clear();
                global_pb.inc(1);
            }));
        }
    }
    for t in tasks {
        t.await.unwrap();
    }
}

async fn download_raw_test_file(client: &Client, g: &TestGroup, file: &RawTestFile) {
    let partial_uuid = file.uuid.split_once("-").unwrap().0;
    let path: PathBuf = ["tests", "data", &g.site, partial_uuid, &file.filename]
        .iter()
        .collect();
    let dir = path.parent().unwrap();
    fs::create_dir_all(dir).unwrap();

    let url = format!(
        "https://cloudnet.fmi.fi/api/download/raw/{}/{}",
        file.uuid, file.filename
    );

    let max_retries = 10;
    let mut attempts = 0;

    let resp = loop {
        if let Ok(resp) = client.get(&url).send().await {
            if resp.status().is_success() {
                break resp;
            }
        };
        if attempts >= max_retries {
            panic!("Failed to donwload {} after {} retries", &url, attempts)
        }
        attempts += 1;
        sleep(Duration::from_secs(10))
    };

    let mut file = File::create(path).unwrap();
    let content = resp.bytes().await.unwrap();
    file.write_all(&content).unwrap();
}

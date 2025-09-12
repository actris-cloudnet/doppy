use std::{
    fs::{create_dir_all, File},
    io::Write,
    path::PathBuf,
};

use reqwest::blocking::get;

use crate::testfile::{find_project_root, get_tests, Testfile};
pub fn download() {
    let tests = get_tests().unwrap();
    for test in tests.testcases {
        for file in test.files {
            download_file(&file);
        }
    }
}

fn download_file(file: &Testfile) {
    let root = find_project_root();
    let uuid_prefix: String = file.uuid.to_string().chars().take(8).collect();
    let path = root
        .join("tests")
        .join("data")
        .join(&file.site_id)
        .join(uuid_prefix)
        .join(&file.filename);
    let resp = get(&file.download_url).unwrap();
    let parent = path.parent().unwrap();
    let b = resp.bytes().unwrap();
    create_dir_all(parent).unwrap();
    let mut f = File::create(&path).unwrap();
    f.write_all(&b).unwrap();
    let p: PathBuf = path
        .iter()
        .rev()
        .take(5)
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect();
    println!("Downloaded {}", p.to_str().unwrap());
}

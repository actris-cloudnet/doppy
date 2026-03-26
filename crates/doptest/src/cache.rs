use std::fs;
use std::path::{Path, PathBuf};

use crate::api::RawRecord;

pub struct FileCache {
    root: PathBuf,
}

impl FileCache {
    pub fn new(root: &Path) -> Self {
        Self {
            root: root.to_path_buf(),
        }
    }

    fn files_dir(&self) -> PathBuf {
        self.root.join("files")
    }

    fn records_dir(&self) -> PathBuf {
        self.root.join("records")
    }

    pub fn file_path(&self, uuid: &str) -> PathBuf {
        self.files_dir().join(uuid)
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    pub fn has_file(&self, uuid: &str) -> bool {
        self.file_path(uuid).exists()
    }

    pub fn store_file(&self, uuid: &str, content: &[u8]) -> Result<(), String> {
        let path = self.file_path(uuid);
        fs::create_dir_all(path.parent().unwrap())
            .map_err(|e| format!("failed to create cache dir: {e}"))?;
        fs::write(&path, content).map_err(|e| format!("failed to write cache file: {e}"))
    }

    pub fn store_records(&self, test_id: &str, records: &[RawRecord]) -> Result<(), String> {
        let dir = self.records_dir();
        fs::create_dir_all(&dir).map_err(|e| format!("failed to create records dir: {e}"))?;
        let path = dir.join(format!("{test_id}.json"));
        let json =
            serde_json::to_string_pretty(records).map_err(|e| format!("serialize error: {e}"))?;
        fs::write(&path, json).map_err(|e| format!("failed to write records: {e}"))
    }

    pub fn load_records(&self, test_id: &str) -> Option<Vec<RawRecord>> {
        let path = self.records_dir().join(format!("{test_id}.json"));
        let text = fs::read_to_string(&path).ok()?;
        serde_json::from_str(&text).ok()
    }
}

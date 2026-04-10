use tokio::process::Command;

use serde::de::DeserializeOwned;

use crate::types::{LockResult, TestEntry};

async fn run_python_helper<T: DeserializeOwned>(module: &str, args: &[&str]) -> Result<T, String> {
    let mut cmd_args = vec!["-m", module];
    cmd_args.extend_from_slice(args);
    let output = Command::new("python")
        .args(&cmd_args)
        .output()
        .await
        .map_err(|e| format!("failed to spawn python: {e}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let detail: &str = if stderr.trim().is_empty() {
            "<no stderr>"
        } else {
            &stderr
        };
        return Err(format!("{module} failed ({}): {detail}", output.status));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout).map_err(|e| format!("parse {module} output: {e}\n{stdout}"))
}

fn build_python_json(entry: &TestEntry, records: &[serde_json::Value]) -> Result<String, String> {
    let mut val = serde_json::to_value(entry).map_err(|e| format!("serialize error: {e}"))?;
    val.as_object_mut().unwrap().insert(
        "records".to_string(),
        serde_json::Value::Array(records.to_vec()),
    );
    serde_json::to_string(&val).map_err(|e| format!("serialize error: {e}"))
}

pub async fn run_lock_helper(
    entry: &TestEntry,
    records: &[serde_json::Value],
) -> Result<LockResult, String> {
    let json = build_python_json(entry, records)?;
    run_python_helper("tests.helpers.lock_helper", &[&json]).await
}

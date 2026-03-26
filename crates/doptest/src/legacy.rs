use std::fmt;
use std::fs;
use std::path::Path;

/// A single legacy test case — a flat bag of key-value pairs from the TOML.
#[derive(Debug, Clone)]
pub struct LegacyCase {
    pub table_name: String,
    pub fields: toml::map::Map<String, toml::Value>,
}

impl LegacyCase {
    pub fn id(&self) -> Option<&str> {
        self.fields.get("id").and_then(|v| v.as_str())
    }

    pub fn site(&self) -> Option<&str> {
        self.fields.get("site").and_then(|v| v.as_str())
    }

    pub fn category(&self) -> &str {
        self.table_name.split('.').next().unwrap_or("")
    }

    pub fn is_slow(&self) -> bool {
        self.fields
            .get("slow")
            .and_then(toml::Value::as_bool)
            .unwrap_or(false)
    }
}

impl fmt::Display for LegacyCase {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut parts = vec![self.table_name.clone()];
        for key in &["site", "date", "filename", "source", "ftype"] {
            if let Some(s) = self.fields.get(*key).and_then(|v| v.as_str()) {
                parts.push(s.to_string());
            }
        }
        let name = parts.join("::");
        if let Some(id) = self.id() {
            write!(f, "[{id}] {name}")
        } else {
            write!(f, "{name}")
        }
    }
}

pub fn read_legacy_config(path: &Path) -> Result<Vec<LegacyCase>, String> {
    let text =
        fs::read_to_string(path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let table: toml::Table =
        toml::from_str(&text).map_err(|e| format!("failed to parse {}: {e}", path.display()))?;

    let mut cases = Vec::new();
    for (category, tests_by_type) in table {
        let by_type = tests_by_type
            .as_table()
            .ok_or_else(|| format!("expected table under '{category}'"))?;
        for (test_type, case_array) in by_type {
            let arr = case_array
                .as_array()
                .ok_or_else(|| format!("expected array at '{category}.{test_type}'"))?;
            let table_name = format!("{category}.{test_type}");
            for item in arr {
                let fields = item
                    .as_table()
                    .ok_or_else(|| format!("expected table entry in '{table_name}'"))?;
                cases.push(LegacyCase {
                    table_name: table_name.clone(),
                    fields: fields.clone(),
                });
            }
        }
    }
    Ok(cases)
}

fn filter_legacy(
    cases: Vec<LegacyCase>,
    category: Option<&str>,
    product: Option<&str>,
    site: Option<&str>,
    source: Option<&str>,
    id: Option<&str>,
    include_slow: bool,
) -> Vec<LegacyCase> {
    cases
        .into_iter()
        .filter(|c| {
            if !include_slow && c.is_slow() {
                return false;
            }
            if let Some(cat) = category
                && c.category() != cat
            {
                return false;
            }
            if let Some(p) = product
                && !c.table_name.contains(p)
            {
                return false;
            }
            if let Some(s) = site
                && c.site() != Some(s)
            {
                return false;
            }
            if let Some(src) = source
                && c.table_name != src
            {
                return false;
            }
            if let Some(i) = id
                && c.id() != Some(i)
            {
                return false;
            }
            true
        })
        .collect()
}

// ── List command ────────────────────────────────────────────────────

pub fn cmd_legacy_list(
    category: Option<&str>,
    product: Option<&str>,
    site: Option<&str>,
    source: Option<&str>,
    id: Option<&str>,
    include_slow: bool,
) -> Result<(), String> {
    let path = Path::new("tests").join("tests-legacy.toml");
    let cases = read_legacy_config(&path)?;
    let filtered = filter_legacy(cases, category, product, site, source, id, include_slow);

    if filtered.is_empty() {
        println!("No legacy tests match the given filters.");
        return Ok(());
    }

    println!("{} legacy test(s):\n", filtered.len());
    for case in &filtered {
        println!("  {case}");
    }
    Ok(())
}

// ── Run command ────────────────────────────────────────────────────

pub async fn cmd_legacy_run(
    category: Option<&str>,
    product: Option<&str>,
    site: Option<&str>,
    source: Option<&str>,
    id: Option<&str>,
    include_slow: bool,
) -> Result<(), String> {
    let mut args: Vec<String> = vec!["-m".into(), "tests".into()];
    if let Some(c) = category {
        args.extend(["--category".into(), c.into()]);
    }
    if let Some(p) = product {
        args.extend(["--product".into(), p.into()]);
    }
    if let Some(s) = site {
        args.extend(["--site".into(), s.into()]);
    }
    if let Some(src) = source {
        args.extend(["--source".into(), src.into()]);
    }
    if let Some(i) = id {
        args.extend(["--id".into(), i.into()]);
    }
    if include_slow {
        args.push("--include-slow".into());
    }

    let status = tokio::process::Command::new("python")
        .args(&args)
        .stdin(std::process::Stdio::inherit())
        .stdout(std::process::Stdio::inherit())
        .stderr(std::process::Stdio::inherit())
        .status()
        .await
        .map_err(|e| format!("failed to spawn python: {e}"))?;

    if status.success() {
        Ok(())
    } else {
        Err(format!(
            "legacy tests failed (exit code: {:?})",
            status.code()
        ))
    }
}

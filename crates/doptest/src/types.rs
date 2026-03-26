use clap::ValueEnum;
use rand::RngExt;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fmt;

pub fn generate_id() -> String {
    const CHARS: &[u8] = b"abcdefghijklmnopqrstuvwxyz0123456789";
    let mut rng = rand::rng();
    (0..6)
        .map(|_| {
            let idx = rng.random_range(0..CHARS.len());
            CHARS[idx] as char
        })
        .collect()
}

// ── Enums ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, ValueEnum)]
#[serde(rename_all = "snake_case")]
pub enum RawKind {
    HaloHpl,
    HaloHplMerge,
    HaloBg,
    HaloSysParams,
    Windcube,
}

impl fmt::Display for RawKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            Self::HaloHpl => "halo_hpl",
            Self::HaloHplMerge => "halo_hpl_merge",
            Self::HaloBg => "halo_bg",
            Self::HaloSysParams => "halo_sys_params",
            Self::Windcube => "windcube",
        };
        f.write_str(s)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, ValueEnum)]
#[serde(rename_all = "snake_case")]
pub enum FileType {
    Vad,
    Dbs,
    Ppi,
    Fixed,
}

impl fmt::Display for FileType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            Self::Vad => "vad",
            Self::Dbs => "dbs",
            Self::Ppi => "ppi",
            Self::Fixed => "fixed",
        };
        f.write_str(s)
    }
}

// ── tests.toml types ────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TestsConfig {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub stare: Vec<StareConfig>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub wind: Vec<WindConfig>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub stare_depol: Vec<StareDepolConfig>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub turbulence: Vec<TurbulenceConfig>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub raw: Vec<RawConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StareConfig {
    pub id: String,
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindConfig {
    pub id: String,
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ftype: Option<FileType>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub options: Option<WindOptionsConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindOptionsConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub azimuth_offset_deg: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StareDepolConfig {
    pub id: String,
    pub site: String,
    pub date: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TurbulenceConfig {
    pub id: String,
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawConfig {
    pub id: String,
    pub kind: RawKind,
    pub site: String,
    pub date: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub filename: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub uuid: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub prefix: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub suffix: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ftype: Option<FileType>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

// ── Unified test entry for JSON exchange with Python ────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "product")]
pub enum TestEntry {
    #[serde(rename = "stare")]
    Stare {
        id: String,
        site: String,
        date: String,
        instrument_id: String,
        instrument_uuid: String,
    },
    #[serde(rename = "wind")]
    Wind {
        id: String,
        site: String,
        date: String,
        instrument_id: String,
        instrument_uuid: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        ftype: Option<FileType>,
        #[serde(skip_serializing_if = "Option::is_none")]
        options: Option<WindOptionsConfig>,
    },
    #[serde(rename = "stare_depol")]
    StareDepol {
        id: String,
        site: String,
        date: String,
    },
    #[serde(rename = "turbulence")]
    Turbulence {
        id: String,
        site: String,
        date: String,
        instrument_id: String,
        instrument_uuid: String,
    },
    #[serde(rename = "raw")]
    Raw {
        id: String,
        kind: RawKind,
        site: String,
        date: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        filename: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        uuid: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        prefix: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        suffix: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        ftype: Option<FileType>,
    },
}

impl TestEntry {
    pub fn id(&self) -> &str {
        match self {
            Self::Stare { id, .. }
            | Self::Wind { id, .. }
            | Self::StareDepol { id, .. }
            | Self::Turbulence { id, .. }
            | Self::Raw { id, .. } => id,
        }
    }

    pub const fn product(&self) -> &str {
        match self {
            Self::Stare { .. } => "stare",
            Self::Wind { .. } => "wind",
            Self::StareDepol { .. } => "stare_depol",
            Self::Turbulence { .. } => "turbulence",
            Self::Raw { .. } => "raw",
        }
    }

    pub fn site(&self) -> &str {
        match self {
            Self::Stare { site, .. }
            | Self::Wind { site, .. }
            | Self::StareDepol { site, .. }
            | Self::Turbulence { site, .. }
            | Self::Raw { site, .. } => site,
        }
    }

    pub fn date(&self) -> &str {
        match self {
            Self::Stare { date, .. }
            | Self::Wind { date, .. }
            | Self::StareDepol { date, .. }
            | Self::Turbulence { date, .. }
            | Self::Raw { date, .. } => date,
        }
    }
}

impl fmt::Display for TestEntry {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Stare {
                id,
                site,
                date,
                instrument_id,
                ..
            } => {
                write!(f, "[{id}] stare {site} {date} ({instrument_id})")
            }
            Self::Wind {
                id,
                site,
                date,
                instrument_id,
                ftype,
                ..
            } => {
                write!(f, "[{id}] wind {site} {date} ({instrument_id}")?;
                if let Some(ft) = ftype {
                    write!(f, ", {ft}")?;
                }
                write!(f, ")")
            }
            Self::StareDepol { id, site, date } => {
                write!(f, "[{id}] stare_depol {site} {date}")
            }
            Self::Turbulence { id, site, date, .. } => {
                write!(f, "[{id}] turbulence {site} {date}")
            }
            Self::Raw {
                id,
                kind,
                site,
                date,
                ..
            } => write!(f, "[{id}] raw:{kind} {site} {date}"),
        }
    }
}

// ── Config → TestEntry conversion ───────────────────────────────────

impl TestsConfig {
    pub fn entries(&self) -> Vec<TestEntry> {
        let mut out = Vec::new();
        for e in &self.stare {
            out.push(TestEntry::Stare {
                id: e.id.clone(),
                site: e.site.clone(),
                date: e.date.clone(),
                instrument_id: e.instrument_id.clone(),
                instrument_uuid: e.instrument_uuid.clone(),
            });
        }
        for e in &self.wind {
            out.push(TestEntry::Wind {
                id: e.id.clone(),
                site: e.site.clone(),
                date: e.date.clone(),
                instrument_id: e.instrument_id.clone(),
                instrument_uuid: e.instrument_uuid.clone(),
                ftype: e.ftype.clone(),
                options: e.options.clone(),
            });
        }
        for e in &self.stare_depol {
            out.push(TestEntry::StareDepol {
                id: e.id.clone(),
                site: e.site.clone(),
                date: e.date.clone(),
            });
        }
        for e in &self.turbulence {
            out.push(TestEntry::Turbulence {
                id: e.id.clone(),
                site: e.site.clone(),
                date: e.date.clone(),
                instrument_id: e.instrument_id.clone(),
                instrument_uuid: e.instrument_uuid.clone(),
            });
        }
        for e in &self.raw {
            out.push(TestEntry::Raw {
                id: e.id.clone(),
                kind: e.kind.clone(),
                site: e.site.clone(),
                date: e.date.clone(),
                filename: e.filename.clone(),
                uuid: e.uuid.clone(),
                prefix: e.prefix.clone(),
                suffix: e.suffix.clone(),
                ftype: e.ftype.clone(),
            });
        }
        out
    }

    pub const fn test_count(&self) -> usize {
        self.stare.len()
            + self.wind.len()
            + self.stare_depol.len()
            + self.turbulence.len()
            + self.raw.len()
    }
}

// ── tests.lock types ────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TestsLock {
    pub meta: LockMeta,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub stare: Vec<LockEntry>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub wind: Vec<LockEntry>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub stare_depol: Vec<LockEntry>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub turbulence: Vec<LockEntry>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub raw: Vec<LockEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct LockMeta {
    pub locked_at: String,
    pub doppy_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LockEntry {
    pub id: String,
    pub site: String,
    pub date: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub instrument_uuid: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub kind: Option<RawKind>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ftype: Option<FileType>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub filename: Option<String>,
    pub input: LockInput,
    pub expect: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LockInput {
    pub files: Vec<InputFile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputFile {
    pub filename: String,
    pub uuid: String,
    pub sha256: String,
}

impl TestsLock {
    fn product_entries(&self) -> [(&str, &[LockEntry]); 5] {
        [
            ("stare", &self.stare),
            ("wind", &self.wind),
            ("stare_depol", &self.stare_depol),
            ("turbulence", &self.turbulence),
            ("raw", &self.raw),
        ]
    }

    pub fn keys(&self) -> HashSet<String> {
        self.product_entries()
            .into_iter()
            .flat_map(|(_, entries)| entries.iter().map(|e| e.id.clone()))
            .collect()
    }

    pub fn find_expect(&self, entry: &TestEntry) -> Option<&serde_json::Value> {
        let target = entry.id();
        let entries: &[LockEntry] = match entry {
            TestEntry::Stare { .. } => &self.stare,
            TestEntry::Wind { .. } => &self.wind,
            TestEntry::StareDepol { .. } => &self.stare_depol,
            TestEntry::Turbulence { .. } => &self.turbulence,
            TestEntry::Raw { .. } => &self.raw,
        };
        entries.iter().find(|e| e.id == target).map(|e| &e.expect)
    }

    pub fn sort_by_ids(&mut self, order: &[&str]) {
        let position = |id: &str| order.iter().position(|&x| x == id).unwrap_or(usize::MAX);
        for vec in [
            &mut self.stare,
            &mut self.wind,
            &mut self.stare_depol,
            &mut self.turbulence,
            &mut self.raw,
        ] {
            vec.sort_by_key(|e| position(&e.id));
        }
    }

    pub fn insert(&mut self, entry: &TestEntry, input: LockInput, expect: serde_json::Value) {
        let lock_entry = LockEntry {
            id: entry.id().to_string(),
            site: entry.site().to_string(),
            date: entry.date().to_string(),
            instrument_uuid: match entry {
                TestEntry::Stare {
                    instrument_uuid, ..
                }
                | TestEntry::Wind {
                    instrument_uuid, ..
                } => Some(instrument_uuid.clone()),
                _ => None,
            },
            kind: match entry {
                TestEntry::Raw { kind, .. } => Some(kind.clone()),
                _ => None,
            },
            ftype: match entry {
                TestEntry::Wind { ftype, .. } | TestEntry::Raw { ftype, .. } => ftype.clone(),
                _ => None,
            },
            filename: match entry {
                TestEntry::Raw { filename, .. } => filename.clone(),
                _ => None,
            },
            input,
            expect,
        };
        let vec = match entry {
            TestEntry::Stare { .. } => &mut self.stare,
            TestEntry::Wind { .. } => &mut self.wind,
            TestEntry::StareDepol { .. } => &mut self.stare_depol,
            TestEntry::Turbulence { .. } => &mut self.turbulence,
            TestEntry::Raw { .. } => &mut self.raw,
        };
        vec.retain(|e| e.id != lock_entry.id);
        vec.push(lock_entry);
    }
}

// ── Python helper result types ──────────────────────────────────────

#[derive(Debug, Clone, Deserialize)]
pub struct LockResult {
    pub input: LockInput,
    pub expect: serde_json::Value,
}

#[derive(Debug, Clone)]
pub struct Diff {
    pub field: String,
    pub expected: serde_json::Value,
    pub actual: serde_json::Value,
}

impl fmt::Display for Diff {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if let (Some(exp), Some(act)) = (self.expected.as_f64(), self.actual.as_f64()) {
            let abs_diff = (act - exp).abs();
            let rel_diff = if exp == 0.0 {
                f64::INFINITY
            } else {
                abs_diff / exp.abs()
            };
            write!(
                f,
                "{}: expected {}, got {} (abs: {:.6e}, rel: {:.6e})",
                self.field, self.expected, self.actual, abs_diff, rel_diff
            )
        } else {
            write!(
                f,
                "{}: expected {}, got {}",
                self.field, self.expected, self.actual
            )
        }
    }
}

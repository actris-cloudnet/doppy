use std::collections::HashSet;
use std::fmt;
use std::fmt::Write as _;
use std::io::Write as IoWrite;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use chrono::Local;
use clap::{Parser, ValueEnum};
use rand::seq::IndexedRandom;
use regex::Regex;
use toml_edit::DocumentMut;

// ── Version ────────────────────────────────────────────────────────

struct Version {
    major: u32,
    minor: u32,
    patch: u32,
}

impl Version {
    fn parse(s: &str) -> Result<Self, String> {
        let parts: Vec<&str> = s.split('.').collect();
        if parts.len() != 3 {
            return Err(format!("invalid version: {s}"));
        }
        Ok(Self {
            major: parts[0]
                .parse()
                .map_err(|_| format!("invalid major: {}", parts[0]))?,
            minor: parts[1]
                .parse()
                .map_err(|_| format!("invalid minor: {}", parts[1]))?,
            patch: parts[2]
                .parse()
                .map_err(|_| format!("invalid patch: {}", parts[2]))?,
        })
    }

    const fn bump(&self, component: Component) -> Self {
        match component {
            Component::Major => Self {
                major: self.major + 1,
                minor: 0,
                patch: 0,
            },
            Component::Minor => Self {
                major: self.major,
                minor: self.minor + 1,
                patch: 0,
            },
            Component::Patch => Self {
                major: self.major,
                minor: self.minor,
                patch: self.patch + 1,
            },
        }
    }

    fn tag(&self) -> String {
        format!("v{self}")
    }
}

impl fmt::Display for Version {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

// ── Git ────────────────────────────────────────────────────────────

struct Git {
    root: PathBuf,
}

impl Git {
    fn new() -> Result<Self, String> {
        let output = Command::new("git")
            .args(["rev-parse", "--show-toplevel"])
            .output()
            .map_err(|e| format!("failed to run git: {e}"))?;
        if !output.status.success() {
            return Err("not in a git repository".into());
        }
        let root = String::from_utf8_lossy(&output.stdout).trim().to_string();
        Ok(Self {
            root: PathBuf::from(root),
        })
    }

    fn git(&self, args: &[&str]) -> Result<String, String> {
        let output = Command::new("git")
            .args(args)
            .current_dir(&self.root)
            .output()
            .map_err(|e| format!("git {}: {e}", args[0]))?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("git {} failed: {stderr}", args[0]));
        }
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    fn current_branch(&self) -> Result<String, String> {
        self.git(&["branch", "--show-current"])
            .map(|s| s.trim().to_string())
    }

    fn changed_files(&self, staged: bool) -> Result<HashSet<String>, String> {
        let mut args = vec!["diff", "--name-only"];
        if staged {
            args.push("--staged");
        }
        let output = self.git(&args)?;
        Ok(output
            .lines()
            .filter(|l| !l.is_empty())
            .map(String::from)
            .collect())
    }

    fn add(&self, path: &str) -> Result<(), String> {
        self.git(&["add", path]).map(drop)
    }

    fn commit(&self, message: &str) -> Result<(), String> {
        self.git(&["commit", "-m", message]).map(drop)
    }

    fn tag(&self, tag: &str) -> Result<(), String> {
        self.git(&["tag", tag]).map(drop)
    }

    fn push(&self, remote: &str, branch: &str, tag: &str) -> Result<(), String> {
        self.git(&["push", remote, branch, tag, "--atomic"])
            .map(drop)
    }

    fn restore(&self) -> Result<(), String> {
        self.git(&["restore", "--staged", "--worktree", "."])
            .map(drop)
    }

    fn commits_since(&self, tag: &str) -> Result<Vec<String>, String> {
        let exists = Command::new("git")
            .args(["rev-parse", "--quiet", "--verify", tag])
            .current_dir(&self.root)
            .output();
        match exists {
            Ok(o) if o.status.success() => {}
            _ => return Ok(Vec::new()),
        }
        let output = self.git(&[
            "log",
            "--pretty=format:%s",
            "--reverse",
            &format!("{tag}.."),
        ])?;
        Ok(output
            .lines()
            .filter(|l| !l.is_empty())
            .map(String::from)
            .collect())
    }
}

// ── Cargo ──────────────────────────────────────────────────────────

fn read_version(path: &Path) -> Result<Version, String> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let doc: DocumentMut = content
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;
    let version_str = doc["workspace"]["package"]["version"]
        .as_str()
        .ok_or("missing [workspace.package] version")?;
    Version::parse(version_str)
}

fn write_version(path: &Path, version: &Version) -> Result<(), String> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let mut doc: DocumentMut = content
        .parse()
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;
    doc["workspace"]["package"]["version"] = toml_edit::value(version.to_string());
    std::fs::write(path, doc.to_string())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))
}

fn update_lockfile(root: &Path) -> Result<(), String> {
    let output = Command::new("cargo")
        .args(["update", "--workspace"])
        .current_dir(root)
        .output()
        .map_err(|e| format!("failed to run cargo update: {e}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("cargo update --workspace failed: {stderr}"));
    }
    Ok(())
}

// ── Changelog ──────────────────────────────────────────────────────

#[allow(clippy::option_if_let_else)]
fn read_changelog(path: &Path) -> Result<(String, String, String), String> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let section_re = Regex::new(r"(?m)^## ").expect("valid regex");
    let unreleased_re = Regex::new(r"(?mi)^## Unreleased\s*$").expect("valid regex");

    if let Some(m) = unreleased_re.find(&content) {
        let prefix = content[..m.start()].trim_end().to_string();
        let after = &content[m.end()..];
        let end = section_re.find(after).map_or(after.len(), |m2| m2.start());
        let body = after[..end].trim().to_string();
        let suffix = after[end..].to_string();
        Ok((prefix, body, suffix))
    } else {
        let split = section_re
            .find(&content)
            .map_or(content.len(), |m| m.start());
        let prefix = content[..split].trim_end().to_string();
        let suffix = content[split..].to_string();
        Ok((prefix, String::new(), suffix))
    }
}

fn open_editor(content: &str) -> Result<String, String> {
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    let tmp_path = std::env::temp_dir().join("rel-changelog.md");

    std::fs::write(&tmp_path, content).map_err(|e| format!("failed to write temp file: {e}"))?;

    let status = Command::new("sh")
        .args(["-c", &format!("{editor} {}", tmp_path.display())])
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .map_err(|e| format!("failed to open editor '{editor}': {e}"))?;

    if !status.success() {
        return Err("editor exited with non-zero status".into());
    }

    std::fs::read_to_string(&tmp_path).map_err(|e| format!("failed to read temp file: {e}"))
}

fn update_changelog(git: &Git, path: &Path, old: &Version, new: &Version) -> Result<(), String> {
    let (prefix, unreleased_body, suffix) = read_changelog(path)?;

    let mut editor_content = format!(
        "# Enter the changelog entry for version {new}.\n\
         # Lines starting with '#' will be ignored.\n"
    );

    let commits = git.commits_since(&old.tag())?;
    if !commits.is_empty() {
        let _ = write!(editor_content, "#\n# Commits since {old}:\n");
        for c in &commits {
            let _ = writeln!(editor_content, "#   {c}");
        }
    }

    if !unreleased_body.is_empty() {
        editor_content += "\n";
        editor_content += &unreleased_body;
        editor_content += "\n";
    }

    let edited = open_editor(&editor_content)?;

    let entry: String = edited
        .lines()
        .skip_while(|line| line.starts_with('#'))
        .collect::<Vec<_>>()
        .join("\n")
        .trim()
        .to_string();

    if entry.is_empty() {
        return Err("changelog entry is empty".into());
    }

    println!("\nChangelog entry:\n\n{entry}\n");
    if !confirm("Use this changelog entry?") {
        return Err("aborted".into());
    }

    let today = Local::now().format("%Y-%m-%d");
    let new_content = format!("{prefix}\n\n## {new} \u{2013} {today}\n\n{entry}\n\n{suffix}");
    std::fs::write(path, new_content)
        .map_err(|e| format!("failed to write {}: {e}", path.display()))
}

// ── Pre-commit ─────────────────────────────────────────────────────

fn precommit(git: &Git) -> Result<(), String> {
    let hook = git.root.join(".git/hooks/pre-commit");
    let result = Command::new(&hook)
        .current_dir(&git.root)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status();

    match result {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(e) => Err(format!("failed to run pre-commit hook: {e}")),
        Ok(s) if s.success() => Ok(()),
        Ok(_) => {
            let unstaged = git.changed_files(false)?;
            let staged = git.changed_files(true)?;

            if !unstaged.is_empty() && unstaged.is_subset(&staged) {
                for file in &unstaged {
                    git.add(file)?;
                }
                Ok(())
            } else {
                git.restore()?;
                Err("pre-commit hook failed".into())
            }
        }
    }
}

// ── CLI ────────────────────────────────────────────────────────────

#[derive(Clone, Copy, ValueEnum)]
enum Component {
    Major,
    Minor,
    Patch,
}

#[derive(Parser)]
struct Cli {
    #[arg(value_enum)]
    component: Component,
}

fn confirm(msg: &str) -> bool {
    print!("{msg} [y/n] ");
    std::io::stdout().flush().ok();
    let mut input = String::new();
    std::io::stdin().read_line(&mut input).ok();
    input.trim().eq_ignore_ascii_case("y")
}

fn congrats() -> &'static str {
    let words = [
        "Spectacular",
        "Phenomenal",
        "Extraordinary",
        "Magnificent",
        "Outstanding",
        "Remarkable",
        "Incredible",
        "Fantastic",
        "Brilliant",
        "Glorious",
    ];
    let mut rng = rand::rng();
    words.choose(&mut rng).unwrap_or(&"Great")
}

fn run() -> Result<(), String> {
    let cli = Cli::parse();

    let git = Git::new()?;
    let branch = git.current_branch()?;
    if branch != "main" {
        return Err(format!("not on 'main' branch (on '{branch}')"));
    }

    let staged = git.changed_files(true)?;
    let unstaged = git.changed_files(false)?;
    if !staged.is_empty() || !unstaged.is_empty() {
        return Err("uncommitted changes detected".into());
    }

    let cargo_toml = git.root.join("Cargo.toml");
    let old = read_version(&cargo_toml)?;
    let new = old.bump(cli.component);

    if !confirm(&format!("Updating version {old} -> {new}. Continue?")) {
        return Ok(());
    }

    write_version(&cargo_toml, &new)?;
    update_lockfile(&git.root)?;

    git.add("Cargo.toml")?;
    git.add("Cargo.lock")?;

    precommit(&git)?;

    let changelog_path = git.root.join("CHANGELOG.md");
    update_changelog(&git, &changelog_path, &old, &new)?;

    git.add("CHANGELOG.md")?;

    precommit(&git)?;

    git.commit(&format!("Release version {new}"))?;
    git.tag(&new.tag())?;
    git.push("origin", "main", &new.tag())?;

    println!("Version {new} released! {} release!", congrats());
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

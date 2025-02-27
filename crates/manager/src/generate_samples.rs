use serde::Deserialize;
use std::fs::File;
use std::io::Write;

use reqwest;

use crate::group;

pub fn sample() {
    let mut file = File::create("filetypes.md").unwrap();

    writeln!(file, "# Filetypes\n").unwrap();

    let groups = group::group();
    let mut groups: Vec<(_, _)> = groups.into_iter().collect();
    groups.sort_by_key(|(k, _)| (k.site.clone(), k.pid.clone()));
    for (group, ftgroups) in groups {
        let h = if let Some(h) = group_to_md_header(&group) {
            h
        } else {
            continue;
        };
        writeln!(file, "## {h}").unwrap();
        let mut ftgroups: Vec<(_, _)> = ftgroups.into_iter().collect();
        ftgroups.sort_by_key(|(k, _)| k.clone());
        for (ft, records) in ftgroups {
            let ft = format!("{:?}", ft);
            writeln!(file, "### {ft}").unwrap();
            let mut records: Vec<_> = records.into_iter().take(10).collect();
            records.sort_by_key(|k| k.filename.clone());
            for r in records {
                let e = record_to_md_entry(&r);
                writeln!(file, "* {e}").unwrap();
            }
            writeln!(file).unwrap();
        }
        writeln!(file).unwrap();
    }
}

#[derive(Debug, Deserialize, Clone)]
#[serde(rename_all = "PascalCase")]
struct InstrumentInfo {
    name: String,
}

fn record_to_md_entry(r: &group::RawRecord) -> String {
    let url = format!(
        "https://cloudnet.fmi.fi/api/download/raw/{}/{}",
        r.uuid, r.filename
    );

    format!("[{}]({})", r.filename, url)
}

fn group_to_md_header(g: &group::InstrumentGroup) -> Option<String> {
    let name = instrument_name_from_uuid(&g.uuid)?;

    Some(format!(
        "[{}](https://cloudnet.fmi.fi/site/{}) - [{}]({})",
        g.site, g.site, name, g.pid
    ))
}

fn instrument_name_from_uuid(uuid: &str) -> Option<String> {
    let url = format!(
        "https://instrumentdb.out.ocp.fmi.fi/instrument/{}.json",
        uuid
    );
    let info = reqwest::blocking::get(url)
        .unwrap()
        .json::<InstrumentInfo>()
        .ok()?;

    Some(info.name)
}

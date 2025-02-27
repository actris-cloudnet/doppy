use serde::Deserialize;
use std::fs::File;
use std::io::Write;

use reqwest;

use crate::group;

pub fn sample() {
    let mut file = File::create("filetypes.md").unwrap();

    writeln!(file, "# Filetypes\n\n").unwrap();

    let groups = group::group();
    let mut groups: Vec<(_, _)> = groups.into_iter().collect();
    groups.sort_by_key(|(k, _)| (k.site.clone(), k.pid.clone(), k.filetype.clone()));
    for (group, records) in groups {
        let h = group_to_md_header(&group);
        writeln!(file, "## {h}\n").unwrap();
        for r in records.into_iter().take(1) {
            let e = record_to_md_entry(&r);
            writeln!(file,"* {e}").unwrap();
        }
        writeln!(file, "\n").unwrap();
    }
}

#[derive(Debug, Deserialize, Clone)]
#[serde(rename_all = "PascalCase")]
struct InstrumentInfo {
    name: String,
}

fn record_to_md_entry(r: &group::RawRecord) -> String{
    let url = format!(
        "https://cloudnet.fmi.fi/api/download/raw/{}/{}",
        r.uuid, r.filename
    );

    format!("[{}]({})", r.filename, url)
}

fn group_to_md_header(g: &group::Group) -> String {
    let name = instrument_name_from_uuid(&g.uuid);

    let ft = format!("{:?}", g.filetype);

    format!(
        "[{}](https://cloudnet.fmi.fi/site/{}) - [{}]({}) - {}",
        g.site, g.site, name, g.pid, ft
    )
}

fn instrument_name_from_uuid(uuid: &str) -> String {
    let url = format!(
        "https://instrumentdb.out.ocp.fmi.fi/instrument/{}.json",
        uuid
    );
    let info = reqwest::blocking::get(url)
        .unwrap()
        .json::<InstrumentInfo>()
        .unwrap();
    info.name
}

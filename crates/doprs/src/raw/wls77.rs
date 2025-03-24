use crate::raw::error::RawParseError;
use chrono::{DateTime, NaiveDateTime, ParseError, Utc};
use std::fs::File;
use std::io::{BufRead, Cursor, Read};

#[derive(Debug, Default, Clone)]
pub struct Wls77 {
    pub info: Info,
    pub data_columns: Vec<String>,
    pub data: Vec<f64>,
}

#[derive(Debug, Default, Clone)]
pub struct Info {
    pub altitude: Vec<f64>,
    pub system_id: String,
    pub cnr_threshold: f64,
}

pub fn from_file_src(mut file: &File) -> Result<Wls77, RawParseError> {
    let mut content = vec![];
    file.read_to_end(&mut content)?;
    from_bytes_src(&content)
}

enum Phase {
    Info,
    Data,
}

pub fn from_bytes_src(content: &[u8]) -> Result<Wls77, RawParseError> {
    let cur = Cursor::new(content);
    let mut info_str = Vec::new();
    let mut header = Vec::new();
    let mut data_str = Vec::new();

    let mut phase = Phase::Info;

    for line in cur.split(b'\n') {
        let line = line.unwrap();
        match phase {
            Phase::Info => {
                if line.starts_with(b"Timestamp\tPosition\tTemperature")
                    || line.starts_with(b"Date\tPosition\tTemperature")
                {
                    header.extend_from_slice(&line);
                    header.push(b'\n');
                    phase = Phase::Data;
                } else {
                    info_str.extend_from_slice(&line);
                    info_str.push(b'\n');
                }
            }
            Phase::Data => {
                data_str.extend_from_slice(&line);
                data_str.push(b'\n');
            }
        }
    }
    let info = parse_info(&info_str)?;

    match parse_data(&data_str) {
        Ok((data, ncols)) => {
            let header_str: String = header.iter().map(|&c| c as char).collect();
            let cols: Vec<_> = header_str
                .split('\t')
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect();
            if ncols != (cols.len() as i64) {
                return Err(RawParseError {
                    message: "Number of columns on header and number of columns in data mismatch"
                        .to_string(),
                });
            }
            Ok(Wls77 {
                info,
                data_columns: cols,
                data,
            })
        }
        Err(e) => Err(e),
    }
}

fn parse_info(info_str: &[u8]) -> Result<Info, RawParseError> {
    let mut info = Info::default();
    for line in info_str.split(|&b| b == b'\n') {
        match line {
            b if b.starts_with(b"Altitudes AGL (m)=") => {
                info.altitude = line
                    .split(|&b| b == b'\t')
                    .skip(1)
                    .map(|part| {
                        String::from_utf8(part.to_vec())
                            .map_err(|_| RawParseError {
                                message: "UTF-8 conversion error".into(),
                            })
                            .and_then(|s| {
                                s.trim().parse::<f64>().map_err(|_| RawParseError {
                                    message: "Parse float error".into(),
                                })
                            })
                    })
                    .collect::<Result<Vec<f64>, _>>()?;
            }
            b if b.starts_with(b"ID System=") => {
                info.system_id = std::str::from_utf8(&line[10..])
                    .map(|s| s.trim())
                    .map_err(|_| RawParseError {
                        message: "UTF-8 conversion error".into(),
                    })?
                    .to_string();
            }
            b if b.starts_with(b"CNRThreshold=") => {
                info.cnr_threshold = std::str::from_utf8(&line[13..])
                    .map_err(|_| RawParseError {
                        message: "UTF-8 conversion error".into(),
                    })?
                    .trim()
                    .parse::<f64>()
                    .map_err(|_| RawParseError {
                        message: "Parse float error".into(),
                    })?;
            }
            _ => (),
        }
    }

    Ok(info)
}

pub fn parse_data(data: &[u8]) -> Result<(Vec<f64>, i64), RawParseError> {
    let mut ncols: i64 = -1;
    let mut data_flat = vec![];
    for line in data.split(|&b| b == b'\n') {
        let parts: Vec<_> = line
            .split(|&b| b == b'\t')
            .filter(|part| !(part.is_empty() || part == b"\r"))
            .collect();
        if parts.is_empty() {
            continue;
        }
        if ncols < 0 {
            ncols = parts.len() as i64;
        }
        if ncols != parts.len() as i64 {
            return Err(RawParseError {
                message: "Unexpected number of columns".to_string(),
            });
        }
        for (i, part) in parts.iter().enumerate() {
            match i {
                0 => {
                    let date = String::from_utf8_lossy(part).trim().to_string();
                    match datetime_to_timestamp(&date) {
                        Ok(d) => {
                            data_flat.push(d);
                        }
                        Err(_) => println!("Error with datetime"),
                    }
                }
                1 => {
                    let s = String::from_utf8_lossy(part).trim().to_string();
                    if let Ok(val) = s.parse::<f64>() {
                        data_flat.push(val);
                    } else {
                        match s.as_ref() {
                            "V" => data_flat.push(-1.0),
                            _ => data_flat.push(-2.0),
                        }
                    }
                }

                _ => match String::from_utf8_lossy(part).trim().parse::<f64>() {
                    Ok(x) => {
                        data_flat.push(x);
                    }
                    Err(_) => println!("Cannot parse float"),
                },
            }
        }
    }
    if ncols < 1 || (data_flat.len() as i64) % ncols != 0 {
        return Err(RawParseError {
            message: "Unexpected number of columns".to_string(),
        });
    }
    Ok((data_flat, ncols))
}
fn datetime_to_timestamp(s: &str) -> Result<f64, ParseError> {
    let format = "%Y/%m/%d %H:%M:%S%.f";
    let ndt = NaiveDateTime::parse_from_str(s, format)?;
    let dt = DateTime::<Utc>::from_naive_utc_and_offset(ndt, Utc);
    Ok(dt.timestamp() as f64 + dt.timestamp_subsec_millis() as f64 / 1000.0)
}

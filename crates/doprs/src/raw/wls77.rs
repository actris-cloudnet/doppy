use crate::raw::error::RawParseError;
use chrono::{DateTime, NaiveDateTime, ParseError, Utc};
use ndarray::{s, Array, Array1, Array2};
use rayon::prelude::*;
use std::fs::File;
use std::io::{BufRead, Cursor, Read};

#[derive(Debug, Default, Clone)]
pub struct Wls77Old {
    pub info: Info,
    pub data_columns: Vec<String>,
    pub data: Vec<f64>,
}

#[derive(Debug, Default, Clone)]
pub struct Wls77 {
    pub time: Array1<f64>,
    pub altitude: Array1<f64>,
    pub position: Array1<f64>,
    pub temperature: Array1<f64>,
    pub wiper_count: Array1<f64>,
    pub cnr: Array2<f64>,
    pub radial_velocity: Array2<f64>,
    pub radial_velocity_deviation: Array2<f64>,
    pub wind_speed: Array2<f64>,
    pub wind_direction: Array2<f64>,
    pub zonal_wind: Array2<f64>,
    pub meridional_wind: Array2<f64>,
    pub vertical_wind: Array2<f64>,
    pub cnr_threshold: f64,
    pub system_id: String,
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

pub fn from_filename_src(filename: String) -> Result<Wls77, RawParseError> {
    let file = File::open(filename)?;
    from_file_src(&file)
}

pub fn from_filename_srcs(filenames: Vec<String>) -> Vec<Wls77> {
    let results = filenames
        .par_iter()
        .filter_map(|filename| from_filename_src(filename.to_string()).ok())
        .collect();
    results
}

pub fn from_file_srcs(files: Vec<&File>) -> Vec<Wls77> {
    let results = files
        .par_iter()
        .filter_map(|file| from_file_src(file).ok())
        .collect();
    results
}

pub fn from_bytes_srcs(contents: Vec<&[u8]>) -> Vec<Wls77> {
    let results = contents
        .par_iter()
        .filter_map(|content| from_bytes_src(content).ok())
        .collect();
    results
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

            let data: Array1<_> = Array::from_vec(data.clone());
            let n = (data.len() as i64 / ncols)
                .try_into()
                .map_err(|e| RawParseError {
                    message: format!("Failed to convert rows count: {e}"),
                })?;
            let m = ncols.try_into().map_err(|e| RawParseError {
                message: format!("Failed to convert columns count: {e}"),
            })?;
            let shape: [usize; 2] = [n, m];

            let data = data
                .into_shape_with_order(shape)
                .map_err(|e| RawParseError {
                    message: format!("Cannot reshape data array: {e}"),
                })?;
            let altitude = Array::from_vec(info.altitude);

            let time = data.slice(s![.., 0]).to_owned();
            let position = data.slice(s![.., 1]).to_owned();
            let temperature = data.slice(s![.., 2]).to_owned();
            let wiper_count = data.slice(s![.., 2]).to_owned();
            let cnr = data.slice(s![..,4..;8]).to_owned();
            let radial_velocity = data.slice(s![..,5..;8]).to_owned();
            let radial_velocity_deviation = data.slice(s![..,6..;8]).to_owned();
            let wind_speed = data.slice(s![..,7..;8]).to_owned();
            let wind_direction = data.slice(s![..,8..;8]).to_owned();
            let zonal_wind = data.slice(s![..,9..;8]).to_owned();
            let meridional_wind = data.slice(s![..,10..;8]).to_owned();
            let vertical_wind = data.slice(s![..,11..;8]).to_owned();

            Ok(Wls77 {
                time,
                altitude,
                position,
                temperature,
                wiper_count,
                cnr,
                radial_velocity,
                radial_velocity_deviation,
                wind_speed,
                wind_direction,
                zonal_wind,
                meridional_wind,
                vertical_wind,
                system_id: info.system_id,
                cnr_threshold: info.cnr_threshold,
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

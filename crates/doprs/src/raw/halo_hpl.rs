extern crate chrono;

use chrono::{DateTime, NaiveDateTime, ParseError, Utc};
use rayon::prelude::*;

use std::fs::File;
use std::io::{BufRead, Cursor, Read, Seek, SeekFrom};

use crate::raw::error::RawParseError;

#[derive(Debug, Default, Clone)]
pub struct HaloHpl {
    pub info: Info,
    pub data: Data,
}

#[derive(Debug, Default, Clone)]
pub struct Info {
    pub filename: String,
    pub gate_points: u64,
    pub nrays: Option<u64>,
    pub nwaypoints: Option<u64>,
    pub ngates: u64,
    pub pulses_per_ray: u64,
    pub range_gate_length: f64,
    pub resolution: f64,
    pub scan_type: String,
    pub focus_range: u64,
    pub start_time: i64, // Unix-timestamp
    pub system_id: String,
    pub instrument_spectral_width: Option<f64>,
}

#[derive(Debug, Default, Clone)]
pub struct Data {
    // 1 Dimensional data, shape (time,)
    pub time: Vec<f64>, // hours since info.start_time
    pub radial_distance: Vec<f64>,
    pub azimuth: Vec<f64>,
    pub elevation: Vec<f64>,
    pub pitch: Option<Vec<f64>>,
    pub roll: Option<Vec<f64>>,
    // 2 Dimensinal data, shape (time, range)
    // such that X[t,r] represented in 1D vec Y[t*r] in "range-major" order
    pub range: Vec<f64>,
    pub radial_velocity: Vec<f64>,
    pub intensity: Vec<f64>,
    pub beta: Vec<f64>,
    pub spectral_width: Option<Vec<f64>>,
}

pub fn from_filename_src(filename: String) -> Result<HaloHpl, RawParseError> {
    let file = File::open(filename)?;
    from_file_src(&file)
}

pub fn from_filename_srcs(filenames: Vec<String>) -> Vec<HaloHpl> {
    let results = filenames
        .par_iter()
        .filter_map(|filename| from_filename_src(filename.to_string()).ok())
        .collect();
    results
}

pub fn from_file_src(mut file: &File) -> Result<HaloHpl, RawParseError> {
    let mut content = vec![];
    file.read_to_end(&mut content)?;
    from_bytes_src(&content)
}

pub fn from_file_srcs(files: Vec<&File>) -> Vec<HaloHpl> {
    let results = files
        .par_iter()
        .filter_map(|file| from_file_src(file).ok())
        .collect();
    results
}

pub fn from_bytes_srcs(contents: Vec<&[u8]>) -> Vec<HaloHpl> {
    let results = contents
        .par_iter()
        .filter_map(|content| from_bytes_src(content).ok())
        .collect();
    results
}

pub fn from_bytes_src(content: &[u8]) -> Result<HaloHpl, RawParseError> {
    let content_without_nulls: Vec<u8> = content.iter().filter(|&&x| x != 0).cloned().collect();
    let mut cur = Cursor::new(content_without_nulls.as_slice());

    let mut buf_header = vec![];

    while cur.read_until(b'*', &mut buf_header)? > 0 {
        if buf_header.ends_with(b"****") {
            cur.read_until(b'\n', &mut buf_header)?;
            break;
        }
    }
    let info = parse_header(&buf_header)?;
    let data = parse_data(&mut cur, info.ngates, info.range_gate_length)?;
    Ok(HaloHpl { info, data })
}

fn parse_data(
    cur: &mut Cursor<&[u8]>,
    ngates: u64,
    range_gate_length: f64,
) -> Result<Data, RawParseError> {
    let (n1d, n2d) = infer_data_shape(cur)?;
    if ngates < 1 || n1d < 3 || n2d < 4 {
        return Err("Unexpected data shape".into());
    }
    let numbers_per_profile = n1d + ngates * n2d;
    let mut data_flat = vec![];
    'outer: for line in cur.split(b'\n') {
        for part in line?
            .split(|&b| b == b' ')
            .filter(|part| !(part.is_empty() || part == b"\r"))
        {
            match std::str::from_utf8(part)?.trim().parse::<f64>() {
                Ok(x) => data_flat.push(x),
                Err(_) => {
                    break 'outer;
                }
            }
        }
    }
    let nfull_profiles = (data_flat.len() as u64) / numbers_per_profile;
    if nfull_profiles == 0 {
        return Err("Zero complete profiles found".into());
    }
    let data_flat = &data_flat[..((numbers_per_profile * nfull_profiles) as usize)];
    let mut data_1d = vec![vec![0f64; nfull_profiles as usize]; n1d as usize];
    let mut data_2d = vec![vec![0f64; (ngates * nfull_profiles) as usize]; n2d as usize];
    let mut k = 0;
    for p in 0..nfull_profiles as usize {
        for var in data_1d.iter_mut() {
            var[p] = data_flat[k];
            k += 1;
        }
        for g in 0..ngates as usize {
            for var in data_2d.iter_mut() {
                var[g + p * ngates as usize] = data_flat[k];
                k += 1;
            }
        }
    }
    let gate: Vec<f64> = (0..ngates).map(|x| x as f64).collect();

    // Fix time overflow
    // (often the last profile of the day cycles 24.xy -> 00.xy)
    for i in 1..data_1d[0].len() {
        if data_1d[0][i] - data_1d[0][i - 1] < -12.0 {
            for j in i..data_1d[0].len() {
                data_1d[0][j] += 24.0;
            }
        }
    }

    Ok(Data {
        time: data_1d[0].clone(),
        radial_distance: gate
            .iter()
            .map(|&x| (x + 0.5) * range_gate_length)
            .collect(),
        azimuth: data_1d[1].clone(),
        elevation: data_1d[2].clone(),
        pitch: if n1d > 3 {
            Some(data_1d[3].clone())
        } else {
            None
        },
        roll: if n1d > 4 {
            Some(data_1d[4].clone())
        } else {
            None
        },
        range: data_2d[0].clone(),
        radial_velocity: data_2d[1].clone(),
        intensity: data_2d[2].clone(),
        beta: data_2d[3].clone(),
        spectral_width: if n2d > 4 {
            Some(data_2d[4].clone())
        } else {
            None
        },
    })
}

fn infer_data_shape(cur: &mut Cursor<&[u8]>) -> Result<(u64, u64), RawParseError> {
    let pos = cur.position();

    let mut line = vec![];
    let mut data_line_length = vec![];

    for _ in 0..2 {
        cur.read_until(b'\n', &mut line)?;
        data_line_length.push(
            line.split(|&b| b == b' ' || b == b'\r' || b == b'\n')
                .filter(|part| !part.is_empty())
                .collect::<Vec<_>>()
                .len() as u64,
        );
        line.clear();
    }

    cur.seek(SeekFrom::Start(pos))?;
    Ok((data_line_length[0], data_line_length[1]))
}

fn parse_header(header_bytes: &[u8]) -> Result<Info, RawParseError> {
    let mut info = Info::default();
    let re = regex::Regex::new(r"^**** Instrument spectral width = (\d+(\.\d+)?)$")?;
    for line in header_bytes
        .split(|&b| b == b'\n')
        .filter(|line| !line.is_empty())
    {
        let parts: Vec<&str> = line
            .split(|&b| b == b'\t')
            .map(|s| match std::str::from_utf8(s) {
                Ok(v) => v.trim(),
                Err(_) => "",
            })
            .collect::<Vec<_>>();
        if parts.len() == 2 {
            let (key, val) = (parts[0], parts[1]);
            match key {
                "Filename:" => info.filename = val.to_string(),
                "System ID:" => info.system_id = val.to_string(),
                "Number of gates:" => info.ngates = val.parse()?,
                "Range gate length (m):" => info.range_gate_length = val.parse()?,
                "Gate length (pts):" => info.gate_points = val.parse()?,
                "Pulses/ray:" => info.pulses_per_ray = val.parse()?,
                "No. of rays in file:" => info.nrays = Some(val.parse()?),
                "No. of waypoints in file:" => info.nwaypoints = Some(val.parse()?),
                "Scan type:" => info.scan_type = val.to_string(),
                "Focus range:" => info.focus_range = val.parse()?,
                "Start time:" => info.start_time = start_time_str_to_datetime(val)?,
                "Resolution (m/s):" => info.resolution = val.parse()?,
                _ => {
                    return Err(
                        format!("Unexpected (key,val) pair in header: ({},{})", key, val).into(),
                    )
                }
            }
        } else {
            let line = std::str::from_utf8(line)?.trim().to_string();
            if let Some(captures) = re.captures(&line) {
                info.instrument_spectral_width = Some(captures[1].parse()?);
            } else {
                match line.as_str() {
                    "Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length" => (),
                    "Range of measurement (center of gate) = (range gate + 0.5) * Gate length" => (),
                    "Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)" => (),
                    "Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees)" => (),
                    "f9.6,1x,f6.2,1x,f6.2" => (),
                    "Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)" => (),
                    "Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) Spectral Width" => (),
                    "i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates" => (),
                    "i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates" => (),
                    "****" => (),
                    _ => return Err(format!("Unexpected header line: {}", line).into()),
                };
            };
        };
    }
    Ok(info)
}

fn start_time_str_to_datetime(s: &str) -> Result<i64, ParseError> {
    let format = "%Y%m%d %H:%M:%S%.f";
    let ndt = NaiveDateTime::parse_from_str(s, format)?;
    Ok(DateTime::<Utc>::from_naive_utc_and_offset(ndt, Utc).timestamp())
}

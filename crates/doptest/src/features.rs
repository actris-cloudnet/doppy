use std::path::Path;

use netcdf::AttributeValue;
use serde::Serialize;

use crate::sample::CachedRecord;

// ── Output types ────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct SampleResult {
    pub uuid: String,
    pub features: Features,
    pub metadata: Metadata,
}

#[derive(Debug, Serialize)]
pub struct Features {
    pub n_timestamps: usize,
    pub n_ranges: usize,
    pub min_height: f64,
    pub max_height: f64,
    pub duration_hours: f64,
    pub median_timediff: f64,
    pub p05_timediff: f64,
    pub p95_timediff: f64,
    pub fraction_masked_beta: f64,
    pub mean_log_beta_raw_signal: f64,
    pub var_log_beta_raw_signal: f64,
    pub mean_log_beta_raw_noise: f64,
    pub var_log_beta_raw_noise: f64,
    pub mean_velocity: f64,
    pub var_velocity: f64,
    pub fraction_masked_velocity: f64,
    pub has_depolarisation: u8,
}

#[derive(Debug, Serialize)]
pub struct Metadata {
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    pub source: String,
    pub wavelength: f64,
    pub pulses_per_ray: i64,
    pub file_uuid: String,
}

impl Features {
    #[allow(clippy::cast_precision_loss)]
    pub fn to_vec(&self) -> Vec<f64> {
        vec![
            self.n_timestamps as f64,
            self.n_ranges as f64,
            self.min_height,
            self.max_height,
            self.duration_hours,
            self.median_timediff,
            self.p05_timediff,
            self.p95_timediff,
            self.fraction_masked_beta,
            self.mean_log_beta_raw_signal,
            self.var_log_beta_raw_signal,
            self.mean_log_beta_raw_noise,
            self.var_log_beta_raw_noise,
            self.mean_velocity,
            self.var_velocity,
            self.fraction_masked_velocity,
            f64::from(self.has_depolarisation),
        ]
    }
}

// ── Statistics helpers ──────────────────────────────────────────────

#[allow(clippy::cast_precision_loss)]
fn mean(data: &[f64]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    data.iter().sum::<f64>() / data.len() as f64
}

#[allow(clippy::cast_precision_loss)]
fn variance(data: &[f64]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let m = mean(data);
    data.iter().map(|&x| (x - m).powi(2)).sum::<f64>() / data.len() as f64
}

fn median_sorted(sorted: &[f64]) -> f64 {
    if sorted.is_empty() {
        return 0.0;
    }
    let n = sorted.len();
    if n % 2 == 1 {
        sorted[n / 2]
    } else {
        f64::midpoint(sorted[n / 2 - 1], sorted[n / 2])
    }
}

#[allow(
    clippy::cast_precision_loss,
    clippy::cast_possible_truncation,
    clippy::cast_sign_loss
)]
fn percentile_sorted(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() {
        return 0.0;
    }
    let n = sorted.len();
    if n == 1 {
        return sorted[0];
    }
    let idx = p / 100.0 * (n - 1) as f64;
    let lo = idx.floor() as usize;
    let hi = idx.ceil() as usize;
    let frac = idx - lo as f64;
    if lo == hi {
        sorted[lo]
    } else {
        sorted[lo].mul_add(1.0 - frac, sorted[hi] * frac)
    }
}

// ── Helpers ─────────────────────────────────────────────────────────

fn get_str_attr(file: &netcdf::File, name: &str) -> String {
    file.attribute(name)
        .and_then(|a| a.value().ok())
        .and_then(|v| match v {
            AttributeValue::Str(s) => Some(s),
            _ => None,
        })
        .unwrap_or_default()
}

// ── Feature extraction ──────────────────────────────────────────────

#[allow(clippy::too_many_lines, clippy::cast_precision_loss)]
pub fn extract_features(path: &Path, record: &CachedRecord) -> Result<SampleResult, String> {
    let file = netcdf::open(path).map_err(|e| format!("open {}: {e}", path.display()))?;

    let n_timestamps = file
        .dimension("time")
        .ok_or("missing 'time' dimension")?
        .len();
    let n_ranges = file
        .dimension("range")
        .ok_or("missing 'range' dimension")?
        .len();

    let time_var = file.variable("time").ok_or("missing 'time' variable")?;
    let time_data: Vec<f64> = time_var
        .get_values(..)
        .map_err(|e| format!("read time: {e}"))?;

    let height_var = file.variable("height").ok_or("missing 'height' variable")?;
    let height_data: Vec<f32> = height_var
        .get_values(..)
        .map_err(|e| format!("read height: {e}"))?;
    let min_height = f64::from(*height_data.first().ok_or("empty height")?);
    let max_height = f64::from(*height_data.last().ok_or("empty height")?);

    let duration_hours = if n_timestamps >= 2 {
        time_data.last().unwrap() - time_data.first().unwrap()
    } else {
        0.0
    };

    let (median_timediff, p05_timediff, p95_timediff) = if n_timestamps >= 2 {
        let mut diffs: Vec<f64> = time_data.windows(2).map(|w| w[1] - w[0]).collect();
        diffs.sort_unstable_by(f64::total_cmp);
        (
            median_sorted(&diffs),
            percentile_sorted(&diffs, 5.0),
            percentile_sorted(&diffs, 95.0),
        )
    } else {
        (0.0, 0.0, 0.0)
    };

    let beta_var = file.variable("beta").ok_or("missing 'beta' variable")?;
    let beta_data: Vec<f32> = beta_var
        .get_values(..)
        .map_err(|e| format!("read beta: {e}"))?;
    let beta_fill: f32 = beta_var.fill_value().ok().flatten().unwrap_or(9.969_21e36);
    let is_fill = |x: f32, fill: f32| (x - fill).abs() < 1.0 || x.is_nan();
    let beta_mask: Vec<bool> = beta_data.iter().map(|&x| is_fill(x, beta_fill)).collect();
    let n_beta = beta_mask.len();
    let n_masked_beta = beta_mask.iter().filter(|&&m| m).count();
    let fraction_masked_beta = if n_beta > 0 {
        n_masked_beta as f64 / n_beta as f64
    } else {
        0.0
    };

    let beta_raw_var = file
        .variable("beta_raw")
        .ok_or("missing 'beta_raw' variable")?;
    let beta_raw_data: Vec<f32> = beta_raw_var
        .get_values(..)
        .map_err(|e| format!("read beta_raw: {e}"))?;

    let signal_log: Vec<f64> = beta_raw_data
        .iter()
        .zip(&beta_mask)
        .filter(|&(_, &m)| !m)
        .map(|(v, _)| f64::from(*v))
        .filter(|v| v.is_finite() && *v > 0.0)
        .map(f64::log10)
        .collect();

    let noise_log: Vec<f64> = beta_raw_data
        .iter()
        .zip(&beta_mask)
        .filter(|&(_, &m)| m)
        .map(|(v, _)| f64::from(*v))
        .filter(|v| v.is_finite() && *v > 0.0)
        .map(f64::log10)
        .collect();

    let v_var = file.variable("v").ok_or("missing 'v' variable")?;
    let v_data: Vec<f32> = v_var.get_values(..).map_err(|e| format!("read v: {e}"))?;
    let v_fill: f32 = v_var.fill_value().ok().flatten().unwrap_or(9.969_21e36);
    let v_mask: Vec<bool> = v_data.iter().map(|&x| is_fill(x, v_fill)).collect();
    let n_v = v_mask.len();
    let n_masked_v = v_mask.iter().filter(|&&m| m).count();
    let fraction_masked_velocity = if n_v > 0 {
        n_masked_v as f64 / n_v as f64
    } else {
        0.0
    };
    let vel_valid: Vec<f64> = v_data
        .iter()
        .zip(&v_mask)
        .filter(|&(_, &m)| !m)
        .map(|(v, _)| f64::from(*v))
        .filter(|v| v.is_finite())
        .collect();

    let has_depolarisation = u8::from(file.variable("depolarisation").is_some());

    let source = get_str_attr(&file, "source");
    let file_uuid = get_str_attr(&file, "file_uuid");

    let wavelength = file
        .variable("wavelength")
        .and_then(|v| v.get_value::<f32, _>(()).ok())
        .map_or(0.0, f64::from);
    let pulses_per_ray = file
        .variable("pulses_per_ray")
        .and_then(|v| v.get_value::<i32, _>(()).ok())
        .map_or(0, i64::from);

    Ok(SampleResult {
        uuid: record.uuid.clone(),
        features: Features {
            n_timestamps,
            n_ranges,
            min_height,
            max_height,
            duration_hours,
            median_timediff,
            p05_timediff,
            p95_timediff,
            fraction_masked_beta,
            mean_log_beta_raw_signal: mean(&signal_log),
            var_log_beta_raw_signal: variance(&signal_log),
            mean_log_beta_raw_noise: mean(&noise_log),
            var_log_beta_raw_noise: variance(&noise_log),
            mean_velocity: mean(&vel_valid),
            var_velocity: variance(&vel_valid),
            fraction_masked_velocity,
            has_depolarisation,
        },
        metadata: Metadata {
            site: record.site_id.clone(),
            date: record.measurement_date.clone(),
            instrument_id: record.instrument_id.clone(),
            instrument_uuid: record.instrument_uuid.clone(),
            source,
            wavelength,
            pulses_per_ray,
            file_uuid,
        },
    })
}

// ── Wind feature extraction ─────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct WindSampleResult {
    pub uuid: String,
    pub features: WindFeatures,
    pub metadata: WindMetadata,
}

#[derive(Debug, Serialize)]
pub struct WindFeatures {
    pub n_timestamps: usize,
    pub n_heights: usize,
    pub min_height: f64,
    pub max_height: f64,
    pub duration_hours: f64,
    pub median_timediff: f64,
    pub p05_timediff: f64,
    pub p95_timediff: f64,
    pub fraction_masked_uwind: f64,
    pub mean_uwind_raw_signal: f64,
    pub var_uwind_raw_signal: f64,
    pub mean_uwind_raw_noise: f64,
    pub var_uwind_raw_noise: f64,
    pub mean_vwind: f64,
    pub var_vwind: f64,
    pub fraction_masked_vwind: f64,
}

#[derive(Debug, Serialize)]
pub struct WindMetadata {
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    pub source: String,
    pub serial_number: String,
    pub file_uuid: String,
}

impl WindFeatures {
    #[allow(clippy::cast_precision_loss)]
    pub fn to_vec(&self) -> Vec<f64> {
        vec![
            self.n_timestamps as f64,
            self.n_heights as f64,
            self.min_height,
            self.max_height,
            self.duration_hours,
            self.median_timediff,
            self.p05_timediff,
            self.p95_timediff,
            self.fraction_masked_uwind,
            self.mean_uwind_raw_signal,
            self.var_uwind_raw_signal,
            self.mean_uwind_raw_noise,
            self.var_uwind_raw_noise,
            self.mean_vwind,
            self.var_vwind,
            self.fraction_masked_vwind,
        ]
    }
}

#[allow(
    clippy::too_many_lines,
    clippy::cast_precision_loss,
    clippy::similar_names
)]
pub fn extract_wind_features(
    path: &Path,
    record: &CachedRecord,
) -> Result<WindSampleResult, String> {
    let file = netcdf::open(path).map_err(|e| format!("open {}: {e}", path.display()))?;

    let n_timestamps = file
        .dimension("time")
        .ok_or("missing 'time' dimension")?
        .len();
    let n_heights = file
        .dimension("height")
        .ok_or("missing 'height' dimension")?
        .len();

    let time_var = file.variable("time").ok_or("missing 'time' variable")?;
    let time_data: Vec<f64> = time_var
        .get_values(..)
        .map_err(|e| format!("read time: {e}"))?;

    let height_var = file.variable("height").ok_or("missing 'height' variable")?;
    let height_data: Vec<f32> = height_var
        .get_values(..)
        .map_err(|e| format!("read height: {e}"))?;
    let min_height = f64::from(*height_data.first().ok_or("empty height")?);
    let max_height = f64::from(*height_data.last().ok_or("empty height")?);

    let duration_hours = if n_timestamps >= 2 {
        time_data.last().unwrap() - time_data.first().unwrap()
    } else {
        0.0
    };

    let (median_timediff, p05_timediff, p95_timediff) = if n_timestamps >= 2 {
        let mut diffs: Vec<f64> = time_data.windows(2).map(|w| w[1] - w[0]).collect();
        diffs.sort_unstable_by(f64::total_cmp);
        (
            median_sorted(&diffs),
            percentile_sorted(&diffs, 5.0),
            percentile_sorted(&diffs, 95.0),
        )
    } else {
        (0.0, 0.0, 0.0)
    };

    let uwind_var = file.variable("uwind").ok_or("missing 'uwind' variable")?;
    let uwind_data: Vec<f32> = uwind_var
        .get_values(..)
        .map_err(|e| format!("read uwind: {e}"))?;
    let uwind_fill: f32 = uwind_var.fill_value().ok().flatten().unwrap_or(9.969_21e36);
    let is_fill = |x: f32, fill: f32| (x - fill).abs() < 1.0 || x.is_nan();
    let uwind_mask: Vec<bool> = uwind_data.iter().map(|&x| is_fill(x, uwind_fill)).collect();
    let n_uwind = uwind_mask.len();
    let n_masked_uwind = uwind_mask.iter().filter(|&&m| m).count();
    let fraction_masked_uwind = if n_uwind > 0 {
        n_masked_uwind as f64 / n_uwind as f64
    } else {
        0.0
    };

    let (uwind_signal, uwind_noise) = if let Some(uwind_raw_var) = file.variable("uwind_raw") {
        let uwind_raw_data: Vec<f32> = uwind_raw_var
            .get_values(..)
            .map_err(|e| format!("read uwind_raw: {e}"))?;

        let signal: Vec<f64> = uwind_raw_data
            .iter()
            .zip(&uwind_mask)
            .filter(|&(_, &m)| !m)
            .map(|(v, _)| f64::from(*v))
            .filter(|v| v.is_finite())
            .collect();

        let noise: Vec<f64> = uwind_raw_data
            .iter()
            .zip(&uwind_mask)
            .filter(|&(_, &m)| m)
            .map(|(v, _)| f64::from(*v))
            .filter(|v| v.is_finite())
            .collect();

        (signal, noise)
    } else {
        let signal: Vec<f64> = uwind_data
            .iter()
            .zip(&uwind_mask)
            .filter(|&(_, &m)| !m)
            .map(|(v, _)| f64::from(*v))
            .filter(|v| v.is_finite())
            .collect();
        (signal, Vec::new())
    };

    let vwind_var = file.variable("vwind").ok_or("missing 'vwind' variable")?;
    let vwind_data: Vec<f32> = vwind_var
        .get_values(..)
        .map_err(|e| format!("read vwind: {e}"))?;
    let vwind_fill: f32 = vwind_var.fill_value().ok().flatten().unwrap_or(9.969_21e36);
    let vwind_mask: Vec<bool> = vwind_data.iter().map(|&x| is_fill(x, vwind_fill)).collect();
    let n_vwind = vwind_mask.len();
    let n_masked_vwind = vwind_mask.iter().filter(|&&m| m).count();
    let fraction_masked_vwind = if n_vwind > 0 {
        n_masked_vwind as f64 / n_vwind as f64
    } else {
        0.0
    };
    let vwind_valid: Vec<f64> = vwind_data
        .iter()
        .zip(&vwind_mask)
        .filter(|&(_, &m)| !m)
        .map(|(v, _)| f64::from(*v))
        .filter(|v| v.is_finite())
        .collect();

    let source = get_str_attr(&file, "source");
    let serial_number = get_str_attr(&file, "serial_number");
    let file_uuid = get_str_attr(&file, "file_uuid");

    Ok(WindSampleResult {
        uuid: record.uuid.clone(),
        features: WindFeatures {
            n_timestamps,
            n_heights,
            min_height,
            max_height,
            duration_hours,
            median_timediff,
            p05_timediff,
            p95_timediff,
            fraction_masked_uwind,
            mean_uwind_raw_signal: mean(&uwind_signal),
            var_uwind_raw_signal: variance(&uwind_signal),
            mean_uwind_raw_noise: mean(&uwind_noise),
            var_uwind_raw_noise: variance(&uwind_noise),
            mean_vwind: mean(&vwind_valid),
            var_vwind: variance(&vwind_valid),
            fraction_masked_vwind,
        },
        metadata: WindMetadata {
            site: record.site_id.clone(),
            date: record.measurement_date.clone(),
            instrument_id: record.instrument_id.clone(),
            instrument_uuid: record.instrument_uuid.clone(),
            source,
            serial_number,
            file_uuid,
        },
    })
}

// ── Turbulence feature extraction ───────────────────────────────────

#[derive(Debug, Serialize)]
pub struct TurbulenceSampleResult {
    pub uuid: String,
    pub features: TurbulenceFeatures,
    pub metadata: TurbulenceMetadata,
}

#[derive(Debug, Serialize)]
pub struct TurbulenceFeatures {
    pub n_timestamps: usize,
    pub n_heights: usize,
    pub min_height: f64,
    pub max_height: f64,
    pub duration_hours: f64,
    pub median_timediff: f64,
    pub p05_timediff: f64,
    pub p95_timediff: f64,
    pub fraction_masked_epsilon: f64,
    pub mean_log_epsilon: f64,
    pub var_log_epsilon: f64,
    pub p05_log_epsilon: f64,
    pub p95_log_epsilon: f64,
    pub ray_accumulation_time: f64,
    pub rolling_window_period: f64,
}

#[derive(Debug, Serialize)]
pub struct TurbulenceMetadata {
    pub site: String,
    pub date: String,
    pub instrument_id: String,
    pub instrument_uuid: String,
    pub source: String,
    pub file_uuid: String,
}

impl TurbulenceFeatures {
    #[allow(clippy::cast_precision_loss)]
    pub fn to_vec(&self) -> Vec<f64> {
        vec![
            self.n_timestamps as f64,
            self.n_heights as f64,
            self.min_height,
            self.max_height,
            self.duration_hours,
            self.median_timediff,
            self.p05_timediff,
            self.p95_timediff,
            self.fraction_masked_epsilon,
            self.mean_log_epsilon,
            self.var_log_epsilon,
            self.p05_log_epsilon,
            self.p95_log_epsilon,
            self.ray_accumulation_time,
            self.rolling_window_period,
        ]
    }
}

#[allow(clippy::too_many_lines, clippy::cast_precision_loss)]
pub fn extract_turbulence_features(
    path: &Path,
    record: &CachedRecord,
) -> Result<TurbulenceSampleResult, String> {
    let file = netcdf::open(path).map_err(|e| format!("open {}: {e}", path.display()))?;

    let n_timestamps = file
        .dimension("time")
        .ok_or("missing 'time' dimension")?
        .len();
    let n_heights = file
        .dimension("height")
        .ok_or("missing 'height' dimension")?
        .len();

    let time_var = file.variable("time").ok_or("missing 'time' variable")?;
    let time_data: Vec<f64> = time_var
        .get_values(..)
        .map_err(|e| format!("read time: {e}"))?;

    let height_var = file.variable("height").ok_or("missing 'height' variable")?;
    let height_data: Vec<f32> = height_var
        .get_values(..)
        .map_err(|e| format!("read height: {e}"))?;
    let min_height = f64::from(*height_data.first().ok_or("empty height")?);
    let max_height = f64::from(*height_data.last().ok_or("empty height")?);

    let duration_hours = if n_timestamps >= 2 {
        time_data.last().unwrap() - time_data.first().unwrap()
    } else {
        0.0
    };

    let (median_timediff, p05_timediff, p95_timediff) = if n_timestamps >= 2 {
        let mut diffs: Vec<f64> = time_data.windows(2).map(|w| w[1] - w[0]).collect();
        diffs.sort_unstable_by(f64::total_cmp);
        (
            median_sorted(&diffs),
            percentile_sorted(&diffs, 5.0),
            percentile_sorted(&diffs, 95.0),
        )
    } else {
        (0.0, 0.0, 0.0)
    };

    let eps_var = file
        .variable("epsilon")
        .ok_or("missing 'epsilon' variable")?;
    let eps_data: Vec<f32> = eps_var
        .get_values(..)
        .map_err(|e| format!("read epsilon: {e}"))?;
    let eps_fill: f32 = eps_var.fill_value().ok().flatten().unwrap_or(9.969_21e36);
    let is_fill = |x: f32, fill: f32| (x - fill).abs() < 1.0 || x.is_nan();
    let eps_mask: Vec<bool> = eps_data.iter().map(|&x| is_fill(x, eps_fill)).collect();
    let n_eps = eps_mask.len();
    let n_masked_eps = eps_mask.iter().filter(|&&m| m).count();
    let fraction_masked_epsilon = if n_eps > 0 {
        n_masked_eps as f64 / n_eps as f64
    } else {
        0.0
    };

    let mut log_eps: Vec<f64> = eps_data
        .iter()
        .zip(&eps_mask)
        .filter(|&(_, &m)| !m)
        .map(|(v, _)| f64::from(*v))
        .filter(|v| v.is_finite() && *v > 0.0)
        .map(f64::log10)
        .collect();
    log_eps.sort_unstable_by(f64::total_cmp);

    let mean_log_epsilon = mean(&log_eps);
    let var_log_epsilon = variance(&log_eps);
    let p05_log_epsilon = percentile_sorted(&log_eps, 5.0);
    let p95_log_epsilon = percentile_sorted(&log_eps, 95.0);

    let ray_accumulation_time = file
        .variable("ray_accumulation_time")
        .and_then(|v| v.get_value::<f32, _>(()).ok())
        .map_or(0.0, f64::from);
    let rolling_window_period = file
        .variable("rolling_window_period")
        .and_then(|v| v.get_value::<f32, _>(()).ok())
        .map_or(0.0, f64::from);

    let source = get_str_attr(&file, "source");
    let file_uuid = get_str_attr(&file, "file_uuid");

    Ok(TurbulenceSampleResult {
        uuid: record.uuid.clone(),
        features: TurbulenceFeatures {
            n_timestamps,
            n_heights,
            min_height,
            max_height,
            duration_hours,
            median_timediff,
            p05_timediff,
            p95_timediff,
            fraction_masked_epsilon,
            mean_log_epsilon,
            var_log_epsilon,
            p05_log_epsilon,
            p95_log_epsilon,
            ray_accumulation_time,
            rolling_window_period,
        },
        metadata: TurbulenceMetadata {
            site: record.site_id.clone(),
            date: record.measurement_date.clone(),
            instrument_id: record.instrument_id.clone(),
            instrument_uuid: record.instrument_uuid.clone(),
            source,
            file_uuid,
        },
    })
}

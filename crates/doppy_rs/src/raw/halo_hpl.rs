use numpy::{PyArray1, ToPyArray};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pymodule]
pub fn halo_hpl(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(from_filename_srcs, m)?)?;
    m.add_function(wrap_pyfunction!(from_filename_src, m)?)?;
    m.add_function(wrap_pyfunction!(from_bytes_srcs, m)?)?;
    m.add_function(wrap_pyfunction!(from_bytes_src, m)?)?;
    Ok(())
}

#[pyfunction]
pub fn from_bytes_srcs<'a>(
    py: Python<'a>,
    contents: Vec<&'a [u8]>,
) -> PyResult<Vec<(&'a PyDict, &'a PyDict)>> {
    let raws = doprs::raw::halo_hpl::from_bytes_srcs(contents);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_pydicts(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_bytes_src<'a>(py: Python<'a>, content: &'a [u8]) -> PyResult<(&'a PyDict, &'a PyDict)> {
    let raw = match doprs::raw::halo_hpl::from_bytes_src(content) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {}",
                e
            )))
        }
    };
    convert_to_pydicts(py, raw)
}

#[pyfunction]
pub fn from_filename_srcs(py: Python, filenames: Vec<String>) -> PyResult<Vec<(&PyDict, &PyDict)>> {
    let raws = doprs::raw::halo_hpl::from_filename_srcs(filenames);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_pydicts(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_filename_src(py: Python, filename: String) -> PyResult<(&PyDict, &PyDict)> {
    let raw = match doprs::raw::halo_hpl::from_filename_src(filename) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {}",
                e
            )))
        }
    };
    convert_to_pydicts(py, raw)
}

fn convert_to_pydicts(
    py: Python,
    raw: doprs::raw::halo_hpl::HaloHpl,
) -> PyResult<(&PyDict, &PyDict)> {
    let info = raw.info;
    let data = raw.data;
    let info_dict = PyDict::new(py);
    let data_dict = PyDict::new(py);
    info_dict.set_item("filename", info.filename)?;
    info_dict.set_item("gate_points", info.gate_points)?;
    info_dict.set_item("nrays", info.nrays)?;
    info_dict.set_item("nwaypoints", info.nwaypoints)?;
    info_dict.set_item("ngates", info.ngates)?;
    info_dict.set_item("pulses_per_ray", info.pulses_per_ray)?;
    info_dict.set_item("range_gate_length", info.range_gate_length)?;
    info_dict.set_item("resolution", info.resolution)?;
    info_dict.set_item("scan_type", info.scan_type)?;
    info_dict.set_item("focus_range", info.focus_range)?;
    info_dict.set_item("start_time", info.start_time)?;
    info_dict.set_item("system_id", info.system_id)?;
    info_dict.set_item("instrument_spectral_width", info.instrument_spectral_width)?;

    let time: &PyArray1<f64> = data.time.as_slice().to_pyarray(py);
    let radial_distance: &PyArray1<f64> = data.radial_distance.as_slice().to_pyarray(py);
    let azimuth: &PyArray1<f64> = data.azimuth.as_slice().to_pyarray(py);
    let elevation: &PyArray1<f64> = data.elevation.as_slice().to_pyarray(py);
    let pitch: Option<&PyArray1<f64>> = match data.pitch {
        Some(v) => Some(v.as_slice().to_pyarray(py)),
        None => None,
    };
    let roll: Option<&PyArray1<f64>> = match data.roll {
        Some(v) => Some(v.as_slice().to_pyarray(py)),
        None => None,
    };
    let range: &PyArray1<f64> = data.range.as_slice().to_pyarray(py);
    let radial_velocity: &PyArray1<f64> = data.radial_velocity.as_slice().to_pyarray(py);
    let intensity: &PyArray1<f64> = data.intensity.as_slice().to_pyarray(py);
    let beta: &PyArray1<f64> = data.beta.as_slice().to_pyarray(py);
    let spectral_width: Option<&PyArray1<f64>> = match data.spectral_width {
        Some(v) => Some(v.as_slice().to_pyarray(py)),
        None => None,
    };
    data_dict.set_item("time", time)?;
    data_dict.set_item("radial_distance", radial_distance)?;
    data_dict.set_item("azimuth", azimuth)?;
    data_dict.set_item("elevation", elevation)?;
    data_dict.set_item("pitch", pitch)?;
    data_dict.set_item("roll", roll)?;
    data_dict.set_item("range", range)?;
    data_dict.set_item("radial_velocity", radial_velocity)?;
    data_dict.set_item("intensity", intensity)?;
    data_dict.set_item("beta", beta)?;
    data_dict.set_item("spectral_width", spectral_width)?;
    Ok((info_dict, data_dict))
}

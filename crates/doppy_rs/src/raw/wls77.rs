use numpy::PyArray1;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pymodule]
pub fn wls77(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(from_bytes_src, m)?)?;
    Ok(())
}

#[pyfunction]
pub fn from_bytes_srcs<'a>(py: Python<'a>, contents: Vec<&'a [u8]>) -> PyResult<Vec<&'a PyDict>> {
    let raws = doprs::raw::wls77::from_bytes_srcs(contents);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_bytes_src<'a>(py: Python<'a>, content: &'a [u8]) -> PyResult<&'a PyDict> {
    let raw = match doprs::raw::wls77::from_bytes_src(content) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {e}"
            )))
        }
    };
    convert_to_python(py, raw)
}

#[pyfunction]
pub fn from_filename_srcs(py: Python<'_>, filenames: Vec<String>) -> PyResult<Vec<&PyDict>> {
    let raws = doprs::raw::wls77::from_filename_srcs(filenames);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_filename_src(py: Python<'_>, filename: String) -> PyResult<&PyDict> {
    let raw = match doprs::raw::wls77::from_filename_src(filename) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {e}"
            )))
        }
    };
    convert_to_python(py, raw)
}

fn convert_to_python(py: Python<'_>, raw: doprs::raw::wls77::Wls77) -> PyResult<&PyDict> {
    let d = PyDict::new(py);

    let fields = [
        ("time", raw.time.as_slice()),
        ("altitude", raw.altitude.as_slice()),
        ("position", raw.position.as_slice()),
        ("temperature", raw.temperature.as_slice()),
        ("wiper_count", raw.wiper_count.as_slice()),
        ("cnr", raw.cnr.as_slice()),
        ("radial_velocity", raw.radial_velocity.as_slice()),
        (
            "radial_velocity_deviation",
            raw.radial_velocity_deviation.as_slice(),
        ),
        ("wind_speed", raw.wind_speed.as_slice()),
        ("wind_direction", raw.wind_direction.as_slice()),
        ("zonal_wind", raw.zonal_wind.as_slice()),
        ("meridional_wind", raw.meridional_wind.as_slice()),
        ("vertical_wind", raw.vertical_wind.as_slice()),
    ];

    for (key, value) in fields {
        d.set_item(key, PyArray1::from_slice(py, value.unwrap()))?;
    }

    d.set_item("cnr_threshold", raw.cnr_threshold)?;
    d.set_item("system_id", raw.system_id)?;

    Ok(d)
}

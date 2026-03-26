use numpy::PyArray1;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pymodule]
pub mod wls77 {
    #[pymodule_export]
    use super::from_bytes_src;
}

#[pyfunction]
fn from_bytes_src<'a>(py: Python<'a>, content: &'a [u8]) -> PyResult<Bound<'a, PyDict>> {
    let raw = doprs::raw::wls77::from_bytes_src(content)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to read files: {e}")))?;
    convert_to_python(py, raw)
}

fn convert_to_python(py: Python<'_>, raw: doprs::raw::wls77::Wls77) -> PyResult<Bound<'_, PyDict>> {
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

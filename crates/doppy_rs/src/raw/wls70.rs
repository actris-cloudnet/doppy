use numpy::{PyArray1, ToPyArray};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedBytes;
use pyo3::types::{PyDict, PyList};

type PyReturnType<'a> = (
    Bound<'a, PyDict>,
    Bound<'a, PyList>,
    Bound<'a, PyArray1<f64>>,
);

#[pymodule]
pub mod wls70 {
    #[pymodule_export]
    use super::from_bytes_src;
    #[pymodule_export]
    use super::from_bytes_srcs;
    #[pymodule_export]
    use super::from_filename_src;
    #[pymodule_export]
    use super::from_filename_srcs;
}

#[pyfunction]
#[allow(clippy::needless_pass_by_value)]
fn from_bytes_srcs(
    py: Python<'_>,
    contents: Vec<PyBackedBytes>,
) -> PyResult<Vec<PyReturnType<'_>>> {
    let contents_refs: Vec<&[u8]> = contents.iter().map(|b| &**b).collect();
    let raws = doprs::raw::wls70::from_bytes_srcs(contents_refs);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
fn from_bytes_src<'a>(py: Python<'a>, content: &'a [u8]) -> PyResult<PyReturnType<'a>> {
    let raw = doprs::raw::wls70::from_bytes_src(content)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to read files: {e}")))?;
    convert_to_python(py, raw)
}

#[pyfunction]
fn from_filename_srcs(py: Python, filenames: Vec<String>) -> PyResult<Vec<PyReturnType>> {
    let raws = doprs::raw::wls70::from_filename_srcs(filenames);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
fn from_filename_src(py: Python, filename: String) -> PyResult<PyReturnType> {
    let raw = doprs::raw::wls70::from_filename_src(filename)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to read files: {e}")))?;
    convert_to_python(py, raw)
}

fn convert_to_python(py: Python, raw: doprs::raw::wls70::Wls70) -> PyResult<PyReturnType> {
    let info_dict = PyDict::new(py);
    info_dict.set_item("altitude", raw.info.altitude.as_slice().to_pyarray(py))?;
    info_dict.set_item("system_id", raw.info.system_id)?;
    info_dict.set_item("cnr_threshold", raw.info.cnr_threshold)?;
    Ok((
        info_dict,
        PyList::new(py, raw.data_columns)?,
        raw.data.as_slice().to_pyarray(py),
    ))
}

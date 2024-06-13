use numpy::{PyArray1, ToPyArray};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

type PyReturnType<'a> = (&'a PyDict, &'a PyList, &'a PyArray1<f64>);

#[pymodule]
pub fn wls70(_py: Python, m: &PyModule) -> PyResult<()> {
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
) -> PyResult<Vec<PyReturnType<'a>>> {
    let raws = doprs::raw::wls70::from_bytes_srcs(contents);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_bytes_src<'a>(py: Python<'a>, content: &'a [u8]) -> PyResult<PyReturnType<'a>> {
    let raw = match doprs::raw::wls70::from_bytes_src(content) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {}",
                e
            )))
        }
    };
    convert_to_python(py, raw)
}

#[pyfunction]
pub fn from_filename_srcs(py: Python, filenames: Vec<String>) -> PyResult<Vec<PyReturnType>> {
    let raws = doprs::raw::wls70::from_filename_srcs(filenames);
    let mut result = Vec::new();
    for raw in raws {
        result.push(convert_to_python(py, raw)?);
    }
    Ok(result)
}

#[pyfunction]
pub fn from_filename_src(py: Python, filename: String) -> PyResult<PyReturnType> {
    let raw = match doprs::raw::wls70::from_filename_src(filename) {
        Ok(raw) => raw,
        Err(e) => {
            return Err(PyRuntimeError::new_err(format!(
                "Failed to read files: {}",
                e
            )))
        }
    };
    convert_to_python(py, raw)
}

fn convert_to_python(py: Python, raw: doprs::raw::wls70::Wls70) -> PyResult<PyReturnType> {
    let info_dict = PyDict::new(py);
    info_dict.set_item("altitude", raw.info.altitude.as_slice().to_pyarray(py))?;
    info_dict.set_item("system_id", raw.info.system_id)?;
    info_dict.set_item("cnr_threshold", raw.info.cnr_threshold)?;
    Ok((
        info_dict,
        PyList::new(py, raw.data_columns),
        raw.data.as_slice().to_pyarray(py),
    ))
}

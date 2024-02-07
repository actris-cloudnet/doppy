use pyo3::prelude::*;
use pyo3::wrap_pymodule;

pub mod raw;

/// A Python module implemented in Rust.
#[pymodule]
fn rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_wrapped(wrap_pymodule!(raw::raw))?;
    Ok(())
}

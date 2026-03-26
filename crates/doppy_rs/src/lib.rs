use pyo3::prelude::*;

mod raw;

#[pymodule(name = "rs")]
mod rs_mod {
    use pyo3::prelude::*;

    #[pymodule_export]
    use super::raw::raw;

    #[pymodule_init]
    fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add("__version__", env!("CARGO_PKG_VERSION"))
    }
}

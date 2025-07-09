use pyo3::prelude::*;

mod escape;
mod unescape;

// Import the functions with their actual names from the modules
use escape::{escape_fn, escape_silent_fn};
use unescape::unescape_fn;

#[pymodule]
fn _rysafe_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(escape_fn, m)?)?;
    m.add_function(wrap_pyfunction!(escape_silent_fn, m)?)?;
    m.add_function(wrap_pyfunction!(unescape_fn, m)?)?;
    m.add("__version__", "0.1.0")?;
    Ok(())
}
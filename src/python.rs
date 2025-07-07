//! Python bindings for the HTML escape library
//! 
//! This module provides PyO3-based Python bindings that expose the Rust
//! HTML escaping functionality to Python with full MarkupSafe API compatibility.

use pyo3::prelude::*;
use pyo3::types::{PyString, PyBytes};
use pyo3::{exceptions, wrap_pyfunction};

use crate::escape::{escape_html, unescape_html, escape_silent};
use crate::error::{validate_input_size, validate_utf8, EscapeError};

/// Escapes HTML/XML special characters in a string
/// 
/// This function replaces characters that have special meaning in HTML/XML
/// with their corresponding HTML entities, preventing XSS attacks.
/// 
/// Args:
///     s: The string to escape. Can be str or bytes.
/// 
/// Returns:
///     str: The escaped string with HTML entities.
/// 
/// Raises:
///     TypeError: If input is not str or bytes.
///     ValueError: If input is too large or contains invalid data.
/// 
/// Examples:
///     >>> escape('<b>Hello & "World"</b>')
///     '&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;'
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn escape(py: Python, s: &PyAny) -> PyResult<String> {
    let text = extract_string_from_any(s)?;
    
    // Validate input
    validate_input_size(&text)?;
    validate_utf8(&text)?;
    
    // Release GIL while processing for better performance
    py.allow_threads(|| Ok(escape_html(&text)))
}

/// Unescapes HTML/XML entities in a string
/// 
/// This function converts HTML entities back to their original characters.
/// It handles standard HTML entities and numeric character references.
/// 
/// Args:
///     s: The string to unescape. Can be str or bytes.
/// 
/// Returns:
///     str: The unescaped string with entities converted to characters.
/// 
/// Raises:
///     TypeError: If input is not str or bytes.
///     ValueError: If input is too large or contains invalid data.
/// 
/// Examples:
///     >>> unescape('&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;')
///     '<b>Hello & "World"</b>'
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn unescape(py: Python, s: &PyAny) -> PyResult<String> {
    let text = extract_string_from_any(s)?;
    
    // Validate input
    validate_input_size(&text)?;
    validate_utf8(&text)?;
    
    // Release GIL while processing for better performance
    py.allow_threads(|| Ok(unescape_html(&text)))
}

/// Escapes HTML but returns None for None input (MarkupSafe compatibility)
/// 
/// This function is identical to `escape()` but handles None input gracefully
/// by returning None, which matches MarkupSafe's `escape_silent` behavior.
/// 
/// Args:
///     s: The string to escape, or None. Can be str, bytes, or None.
/// 
/// Returns:
///     str or None: The escaped string, or None if input was None.
/// 
/// Examples:
///     >>> escape_silent('<b>test</b>')
///     '&lt;b&gt;test&lt;/b&gt;'
///     >>> escape_silent(None)
///     
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn escape_silent_py(py: Python, s: &PyAny) -> PyResult<Option<String>> {
    if s.is_none() {
        return Ok(None);
    }
    
    let text = extract_string_from_any(s)?;
    
    // Validate input
    validate_input_size(&text)?;
    validate_utf8(&text)?;
    
    // Release GIL while processing
    py.allow_threads(|| Ok(Some(escape_html(&text))))
}

/// Extracts a string from PyAny, handling both str and bytes inputs
fn extract_string_from_any(obj: &PyAny) -> PyResult<String> {
    if let Ok(py_str) = obj.downcast::<PyString>() {
        // Handle string input
        Ok(py_str.to_str()?.to_string())
    } else if let Ok(py_bytes) = obj.downcast::<PyBytes>() {
        // Handle bytes input - convert to UTF-8 string
        let bytes = py_bytes.as_bytes();
        match std::str::from_utf8(bytes) {
            Ok(s) => Ok(s.to_string()),
            Err(e) => Err(exceptions::PyValueError::new_err(format!(
                "Invalid UTF-8 in bytes input: {}", e
            )))
        }
    } else {
        // Handle invalid input type
        let type_name = obj.get_type().name()?;
        Err(exceptions::PyTypeError::new_err(format!(
            "Expected str or bytes, got {}", type_name
        )))
    }
}

/// Creates the Python module
/// 
/// This function defines the Python module structure and exports all
/// public functions. It's called by PyO3's module initialization.
#[pymodule]
fn rust_html_escape(_py: Python, m: &PyModule) -> PyResult<()> {
    // Add version information
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "Rust HTML Escape Library")?;
    m.add("__doc__", "High-performance HTML/XML escaping library implemented in Rust")?;
    
    // Add core functions
    m.add_function(wrap_pyfunction!(escape, m)?)?;
    m.add_function(wrap_pyfunction!(unescape, m)?)?;
    m.add_function(wrap_pyfunction!(escape_silent_py, m)?)?;
    
    // Add alias for MarkupSafe compatibility
    m.add("escape_silent", m.getattr("escape_silent_py")?)?;
    
    // Add constants
    m.add("MAX_INPUT_SIZE", crate::error::MAX_INPUT_SIZE)?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyString, PyBytes};

    #[test]
    fn test_extract_string_from_str() {
        Python::with_gil(|py| {
            let py_str = PyString::new(py, "hello world");
            let result = extract_string_from_any(py_str.as_ref()).unwrap();
            assert_eq!(result, "hello world");
        });
    }

    #[test]
    fn test_extract_string_from_bytes() {
        Python::with_gil(|py| {
            let py_bytes = PyBytes::new(py, b"hello world");
            let result = extract_string_from_any(py_bytes.as_ref()).unwrap();
            assert_eq!(result, "hello world");
        });
    }

    #[test]
    fn test_extract_string_from_invalid_bytes() {
        Python::with_gil(|py| {
            let invalid_utf8 = [0xFF, 0xFE, 0xFD];
            let py_bytes = PyBytes::new(py, &invalid_utf8);
            let result = extract_string_from_any(py_bytes.as_ref());
            assert!(result.is_err());
        });
    }

    #[test]
    fn test_python_escape() {
        Python::with_gil(|py| {
            let py_str = PyString::new(py, "<b>test</b>");
            let result = escape(py, py_str.as_ref()).unwrap();
            assert_eq!(result, "&lt;b&gt;test&lt;/b&gt;");
        });
    }

    #[test]
    fn test_python_unescape() {
        Python::with_gil(|py| {
            let py_str = PyString::new(py, "&lt;b&gt;test&lt;/b&gt;");
            let result = unescape(py, py_str.as_ref()).unwrap();
            assert_eq!(result, "<b>test</b>");
        });
    }

    #[test]
    fn test_escape_silent_with_none() {
        Python::with_gil(|py| {
            let none = py.None();
            let result = escape_silent_py(py, none.as_ref()).unwrap();
            assert_eq!(result, None);
        });
    }

    #[test]
    fn test_escape_silent_with_string() {
        Python::with_gil(|py| {
            let py_str = PyString::new(py, "<b>test</b>");
            let result = escape_silent_py(py, py_str.as_ref()).unwrap();
            assert_eq!(result, Some("&lt;b&gt;test&lt;/b&gt;".to_string()));
        });
    }

    #[test]
    fn test_invalid_input_type() {
        Python::with_gil(|py| {
            let py_int = py.eval("42", None, None).unwrap();
            let result = extract_string_from_any(py_int);
            assert!(result.is_err());
        });
    }
}
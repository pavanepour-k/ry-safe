//! Python bindings for rysafe.
//!
//! This module provides Python-compatible functions that mirror the MarkupSafe API.
//! All functions handle both string and bytes input, with proper error handling
//! and exception mapping.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString};
use std::borrow::Cow;

// Import from our escape module
use crate::escape::{escape_html, escape_html_bytes, unescape_html, unescape_html_bytes};

/// Extract string or bytes from Python object.
fn extract_string_or_bytes(obj: &PyAny) -> PyResult<StringOrBytes> {
    if let Ok(s) = obj.downcast::<PyString>() {
        Ok(StringOrBytes::String(s.to_str()?.to_string()))
    } else if let Ok(b) = obj.downcast::<PyBytes>() {
        Ok(StringOrBytes::Bytes(b.as_bytes().to_vec()))
    } else {
        Err(PyTypeError::new_err("Expected str or bytes object"))
    }
}

#[derive(Debug)]
enum StringOrBytes {
    String(String),
    Bytes(Vec<u8>),
}

/// Escape HTML characters in a string or bytes object.
///
/// This function converts the characters `&`, `<`, `>`, `'`, and `"` in string
/// to HTML-safe sequences. Use this if you need to display text that might
/// contain such characters in HTML.
///
/// Args:
///     s: The string or bytes to escape.
///
/// Returns:
///     The escaped string or bytes.
///
/// Raises:
///     TypeError: If the input is neither str nor bytes.
///
/// Examples:
///     >>> escape('<script>alert("xss")</script>')
///     '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
///     >>> escape(b'<b>bold</b>')
///     b'&lt;b&gt;bold&lt;/b&gt;'
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn escape(py: Python, s: &PyAny) -> PyResult<PyObject> {
    let input = extract_string_or_bytes(s)?;

    // Release GIL for computational work
    let result = py.allow_threads(|| match input {
        StringOrBytes::String(text) => {
            let escaped = escape_html(&text);
            Ok(StringOrBytes::String(escaped.into_owned()))
        }
        StringOrBytes::Bytes(bytes) => {
            let escaped = escape_html_bytes(&bytes);
            Ok(StringOrBytes::Bytes(escaped))
        }
    })?;

    match result {
        StringOrBytes::String(text) => Ok(PyString::new(py, &text).into()),
        StringOrBytes::Bytes(bytes) => Ok(PyBytes::new(py, &bytes).into()),
    }
}

/// Like escape but passes None through unchanged.
///
/// This is useful for template engines that want to allow None values
/// to pass through unchanged.
///
/// Args:
///     s: The string, bytes, or None to escape.
///
/// Returns:
///     The escaped string/bytes, or None if input was None.
///
/// Examples:
///     >>> escape_silent('<script>')
///     '&lt;script&gt;'
///     >>> escape_silent(None)
///     None
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn escape_silent(py: Python, s: &PyAny) -> PyResult<PyObject> {
    if s.is_none() {
        Ok(py.None())
    } else {
        escape(py, s)
    }
}

/// Unescape HTML entities in a string or bytes object.
///
/// This reverses the escaping performed by `escape()`. It converts HTML
/// entities back to their original characters.
///
/// Args:
///     s: The string or bytes to unescape.
///
/// Returns:
///     The unescaped string or bytes.
///
/// Raises:
///     TypeError: If the input is neither str nor bytes.
///
/// Examples:
///     >>> unescape('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
///     '<script>alert("xss")</script>'
///     >>> unescape(b'&lt;b&gt;bold&lt;/b&gt;')
///     b'<b>bold</b>'
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
pub fn unescape(py: Python, s: &PyAny) -> PyResult<PyObject> {
    let input = extract_string_or_bytes(s)?;

    // Release GIL for computational work
    let result = py.allow_threads(|| match input {
        StringOrBytes::String(text) => {
            let unescaped = unescape_html(&text);
            Ok(StringOrBytes::String(unescaped.into_owned()))
        }
        StringOrBytes::Bytes(bytes) => {
            let unescaped = unescape_html_bytes(&bytes);
            Ok(StringOrBytes::Bytes(unescaped))
        }
    })?;

    match result {
        StringOrBytes::String(text) => Ok(PyString::new(py, &text).into()),
        StringOrBytes::Bytes(bytes) => Ok(PyBytes::new(py, &bytes).into()),
    }
}

/// MarkupSafe-compatible Markup class.
///
/// A string that is ready to be safely inserted into an HTML or XML
/// document, either because it was escaped or because it was marked
/// as safe. Passing an object to this calls escape() on it and
/// wraps the result in a Markup object.
#[pyclass(name = "Markup")]
pub struct MarkupClass {
    content: String,
}

#[pymethods]
impl MarkupClass {
    #[new]
    fn new(py: Python, content: &PyAny) -> PyResult<Self> {
        let escaped = escape(py, content)?;
        let content_str = if let Ok(s) = escaped.downcast::<PyString>(py) {
            s.to_str()?.to_string()
        } else {
            return Err(PyTypeError::new_err("Markup content must be a string"));
        };

        Ok(MarkupClass {
            content: content_str,
        })
    }

    fn __str__(&self) -> &str {
        &self.content
    }

    fn __repr__(&self) -> String {
        format!("Markup('{}')", self.content)
    }

    fn __add__(&self, other: &PyAny) -> PyResult<MarkupClass> {
        if let Ok(other_markup) = other.downcast::<MarkupClass>() {
            Ok(MarkupClass {
                content: format!("{}{}", self.content, other_markup.content),
            })
        } else if let Ok(other_str) = other.downcast::<PyString>() {
            let escaped_other = escape_html(other_str.to_str()?);
            Ok(MarkupClass {
                content: format!("{}{}", self.content, escaped_other),
            })
        } else {
            Err(PyTypeError::new_err("Cannot add non-string to Markup"))
        }
    }

    /// Check if the markup is safe (always True for Markup objects).
    #[getter]
    fn __html__(&self) -> &str {
        &self.content
    }
}

/// Create the Python module.
#[pymodule]
fn _rysafe(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(escape, m)?)?;
    m.add_function(wrap_pyfunction!(escape_silent, m)?)?;
    m.add_function(wrap_pyfunction!(unescape, m)?)?;
    m.add_class::<MarkupClass>()?;

    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "rysafe contributors")?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyBytes, PyString};

    #[test]
    fn test_extract_string_or_bytes() {
        Python::with_gil(|py| {
            // Test string extraction
            let py_str = PyString::new(py, "hello");
            let result = extract_string_or_bytes(py_str).unwrap();
            if let StringOrBytes::String(s) = result {
                assert_eq!(s, "hello");
            } else {
                panic!("Expected String variant");
            }

            // Test bytes extraction
            let py_bytes = PyBytes::new(py, b"hello");
            let result = extract_string_or_bytes(py_bytes).unwrap();
            if let StringOrBytes::Bytes(b) = result {
                assert_eq!(b, b"hello");
            } else {
                panic!("Expected Bytes variant");
            }
        });
    }

    #[test]
    fn test_escape_function() {
        Python::with_gil(|py| {
            let input = PyString::new(py, "<script>alert('xss')</script>");
            let result = escape(py, input).unwrap();
            let result_str = result.downcast::<PyString>(py).unwrap().to_str().unwrap();
            assert_eq!(
                result_str,
                "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
            );
        });
    }

    #[test]
    fn test_escape_bytes() {
        Python::with_gil(|py| {
            let input = PyBytes::new(py, b"<script>");
            let result = escape(py, input).unwrap();
            let result_bytes = result.downcast::<PyBytes>(py).unwrap().as_bytes();
            assert_eq!(result_bytes, b"&lt;script&gt;");
        });
    }

    #[test]
    fn test_unescape_function() {
        Python::with_gil(|py| {
            let input = PyString::new(py, "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;");
            let result = unescape(py, input).unwrap();
            let result_str = result.downcast::<PyString>(py).unwrap().to_str().unwrap();
            assert_eq!(result_str, "<script>alert('xss')</script>");
        });
    }

    #[test]
    fn test_escape_silent_with_none() {
        Python::with_gil(|py| {
            let none = py.None();
            let result = escape_silent(py, none).unwrap();
            assert!(result.is_none(py));
        });
    }

    #[test]
    fn test_markup_class() {
        Python::with_gil(|py| {
            let input = PyString::new(py, "<script>");
            let markup = MarkupClass::new(py, input).unwrap();
            assert_eq!(markup.__str__(), "&lt;script&gt;");
            assert_eq!(markup.__repr__(), "Markup('&lt;script&gt;')");
        });
    }
}
//! Error types and conversions for HTML escaping operations
//! 
//! This module defines error types used throughout the library and provides
//! conversions to Python exceptions for the PyO3 bindings.

use std::fmt;

/// Errors that can occur during HTML escaping/unescaping operations
#[derive(Debug, Clone, PartialEq)]
pub enum EscapeError {
    /// Invalid input type was provided
    InvalidInputType(String),
    /// Input string contains invalid UTF-8 sequences
    InvalidUtf8(String),
    /// Input is too large to process safely
    InputTooLarge(usize),
    /// Generic processing error
    ProcessingError(String),
}

impl fmt::Display for EscapeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EscapeError::InvalidInputType(msg) => {
                write!(f, "Invalid input type: {}", msg)
            }
            EscapeError::InvalidUtf8(msg) => {
                write!(f, "Invalid UTF-8 sequence: {}", msg)
            }
            EscapeError::InputTooLarge(size) => {
                write!(f, "Input too large: {} bytes (max allowed: {})", size, MAX_INPUT_SIZE)
            }
            EscapeError::ProcessingError(msg) => {
                write!(f, "Processing error: {}", msg)
            }
        }
    }
}

impl std::error::Error for EscapeError {}

/// Maximum input size to prevent memory exhaustion attacks
pub const MAX_INPUT_SIZE: usize = 10 * 1024 * 1024; // 10MB

/// Validates input size to prevent memory exhaustion
pub fn validate_input_size(input: &str) -> Result<(), EscapeError> {
    if input.len() > MAX_INPUT_SIZE {
        Err(EscapeError::InputTooLarge(input.len()))
    } else {
        Ok(())
    }
}

/// Validates that input is valid UTF-8 (though Rust strings are always valid UTF-8)
pub fn validate_utf8(input: &str) -> Result<(), EscapeError> {
    // Rust strings are always valid UTF-8, but we include this for completeness
    // and future byte string support
    if input.is_empty() {
        return Ok(());
    }
    
    // Additional validation for null bytes which might cause issues in some contexts
    if input.contains('\0') {
        return Err(EscapeError::InvalidUtf8(
            "Input contains null bytes".to_string()
        ));
    }
    
    Ok(())
}

#[cfg(feature = "python")]
use pyo3::{exceptions, PyErr};

#[cfg(feature = "python")]
impl From<EscapeError> for PyErr {
    fn from(err: EscapeError) -> PyErr {
        match err {
            EscapeError::InvalidInputType(msg) => {
                exceptions::PyTypeError::new_err(format!("Invalid input type: {}", msg))
            }
            EscapeError::InvalidUtf8(msg) => {
                exceptions::PyValueError::new_err(format!("Invalid UTF-8: {}", msg))
            }
            EscapeError::InputTooLarge(size) => {
                exceptions::PyValueError::new_err(format!(
                    "Input too large: {} bytes (max: {})", 
                    size, 
                    MAX_INPUT_SIZE
                ))
            }
            EscapeError::ProcessingError(msg) => {
                exceptions::PyRuntimeError::new_err(format!("Processing error: {}", msg))
            }
        }
    }
}

/// Result type alias for escape operations
pub type EscapeResult<T> = Result<T, EscapeError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_input_size() {
        // Valid size
        assert!(validate_input_size("hello").is_ok());
        
        // Too large (simulate with a large string)
        let large_string = "a".repeat(MAX_INPUT_SIZE + 1);
        assert!(validate_input_size(&large_string).is_err());
    }

    #[test]
    fn test_validate_utf8() {
        // Valid UTF-8
        assert!(validate_utf8("hello world").is_ok());
        assert!(validate_utf8("🌍 world").is_ok());
        assert!(validate_utf8("").is_ok());
        
        // Invalid (contains null byte)
        assert!(validate_utf8("hello\0world").is_err());
    }

    #[test]
    fn test_error_display() {
        let err = EscapeError::InvalidInputType("not a string".to_string());
        assert_eq!(err.to_string(), "Invalid input type: not a string");
        
        let err = EscapeError::InputTooLarge(1000);
        assert!(err.to_string().contains("Input too large: 1000 bytes"));
    }

    #[test]
    fn test_error_equality() {
        let err1 = EscapeError::InvalidInputType("test".to_string());
        let err2 = EscapeError::InvalidInputType("test".to_string());
        let err3 = EscapeError::InvalidInputType("different".to_string());
        
        assert_eq!(err1, err2);
        assert_ne!(err1, err3);
    }

    #[cfg(feature = "python")]
    #[test]
    fn test_python_error_conversion() {
        use pyo3::Python;
        
        Python::with_gil(|py| {
            let err = EscapeError::InvalidInputType("test".to_string());
            let py_err: PyErr = err.into();
            assert!(py_err.is_instance_of::<exceptions::PyTypeError>(py));
        });
    }
}
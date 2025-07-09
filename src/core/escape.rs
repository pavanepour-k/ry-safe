use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

// Removed unused ESCAPE_TABLE constant since we're using match statements directly

#[pyfunction]
#[pyo3(name = "escape")]
pub fn escape_fn(text: &str) -> PyResult<String> {
    if text.is_empty() {
        return Ok(String::new());
    }

    let mut result = String::with_capacity(text.len() * 2);

    for ch in text.chars() {
        match ch {
            '&' => result.push_str("&amp;"),
            '<' => result.push_str("&lt;"),
            '>' => result.push_str("&gt;"),
            '"' => result.push_str("&quot;"),
            '\'' => result.push_str("&#x27;"),
            _ => {
                if ch.is_control() && ch != '\t' && ch != '\n' && ch != '\r' {
                    return Err(PyValueError::new_err(format!(
                        "Invalid control character: U+{:04X}",
                        ch as u32
                    )));
                }
                result.push(ch);
            }
        }
    }

    Ok(result)
}

#[pyfunction]
#[pyo3(name = "escape_silent")]
pub fn escape_silent_fn(text: &str) -> String {
    if text.is_empty() {
        return String::new();
    }

    let mut result = String::with_capacity(text.len() * 2);

    for ch in text.chars() {
        match ch {
            '&' => result.push_str("&amp;"),
            '<' => result.push_str("&lt;"),
            '>' => result.push_str("&gt;"),
            '"' => result.push_str("&quot;"),
            '\'' => result.push_str("&#x27;"),
            _ => {
                if !ch.is_control() || ch == '\t' || ch == '\n' || ch == '\r' {
                    result.push(ch);
                }
            }
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_escape_basic() {
        assert_eq!(escape_fn("").unwrap(), "");
        assert_eq!(escape_fn("hello").unwrap(), "hello");
        assert_eq!(escape_fn("<>&\"'").unwrap(), "&lt;&gt;&amp;&quot;&#x27;");
    }

    #[test]
    fn test_escape_mixed() {
        assert_eq!(
            escape_fn("Hello <world> & \"friends\"").unwrap(),
            "Hello &lt;world&gt; &amp; &quot;friends&quot;"
        );
    }

    #[test]
    fn test_escape_unicode() {
        assert_eq!(escape_fn("café").unwrap(), "café");
        assert_eq!(escape_fn("🦀").unwrap(), "🦀");
    }

    #[test]
    fn test_escape_control_chars() {
        assert!(escape_fn("\x00").is_err());
        assert!(escape_fn("\x1F").is_err());
        assert_eq!(escape_fn("\t\n\r").unwrap(), "\t\n\r");
    }
}
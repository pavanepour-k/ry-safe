//! Rust HTML Escape Library
//! 
//! A high-performance HTML/XML escaping library implemented in Rust with Python bindings.
//! Provides 100% API compatibility with Python's MarkupSafe library while offering
//! significant performance improvements.
//! 
//! # Features
//! 
//! - Fast HTML/XML escaping and unescaping
//! - Full MarkupSafe API compatibility
//! - Python bindings via PyO3
//! - FastAPI integration support
//! - Robust Unicode and edge case handling
//! - Memory-safe with comprehensive input validation
//! 
//! # Usage (Rust)
//! 
//! ```rust
//! use rust_html_escape::{escape_html, unescape_html};
//! 
//! let escaped = escape_html("<b>Hello & \"World\"</b>");
//! assert_eq!(escaped, "&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;");
//! 
//! let unescaped = unescape_html("&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;");
//! assert_eq!(unescaped, "<b>Hello & \"World\"</b>");
//! ```
//! 
//! # Usage (Python)
//! 
//! ```python
//! from rust_html_escape import escape, unescape
//! 
//! escaped = escape('<b>Hello & "World"</b>')
//! assert escaped == '&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;'
//! 
//! unescaped = unescape('&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;')
//! assert unescaped == '<b>Hello & "World"</b>'
//! ```

#![doc(html_root_url = "https://docs.rs/rust-html-escape/")]
#![warn(missing_docs)]
#![warn(rust_2018_idioms)]

pub mod escape;
pub mod error;

// Re-export main functions for easy access
pub use escape::{escape_html, unescape_html, escape_silent};
pub use error::{EscapeError, EscapeResult, MAX_INPUT_SIZE};

// Python bindings (only compiled when python feature is enabled)
#[cfg(feature = "python")]
pub mod python;

#[cfg(feature = "python")]
pub use python::rust_html_escape;

/// Library version from Cargo.toml
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Library name
pub const NAME: &str = env!("CARGO_PKG_NAME");

/// Library description
pub const DESCRIPTION: &str = env!("CARGO_PKG_DESCRIPTION");

#[cfg(test)]
mod integration_tests {
    use super::*;

    #[test]
    fn test_library_constants() {
        assert!(!VERSION.is_empty());
        assert!(!NAME.is_empty());
        assert!(!DESCRIPTION.is_empty());
    }

    #[test]
    fn test_public_api() {
        // Test that all public functions are accessible
        let input = "<b>test & \"quotes\"</b>";
        let escaped = escape_html(input);
        let unescaped = unescape_html(&escaped);
        assert_eq!(input, unescaped);
        
        // Test escape_silent
        assert_eq!(escape_silent(Some(input)), Some(escaped.clone()));
        assert_eq!(escape_silent(None), None);
    }

    #[test]
    fn test_error_types() {
        use error::*;
        
        // Test that error types are accessible
        let _result: EscapeResult<()> = Err(EscapeError::ProcessingError("test".to_string()));
        assert_eq!(MAX_INPUT_SIZE, 10 * 1024 * 1024);
    }

    #[test]
    fn test_markupsafe_compatibility() {
        // Test cases that should match MarkupSafe exactly
        let test_cases = vec![
            ("", ""),
            ("hello", "hello"),
            ("<", "&lt;"),
            (">", "&gt;"),
            ("&", "&amp;"),
            ("\"", "&quot;"),
            ("'", "&#x27;"),
            ("<b>hello</b>", "&lt;b&gt;hello&lt;/b&gt;"),
            ("Ben & Jerry's", "Ben &amp; Jerry&#x27;s"),
            ("<script>alert(\"XSS\")</script>", "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;"),
        ];

        for (input, expected) in test_cases {
            assert_eq!(escape_html(input), expected);
        }
    }

    #[test]
    fn test_unicode_edge_cases() {
        // Test Unicode handling
        let unicode_input = "Hello 世界 🌍 <test>";
        let escaped = escape_html(unicode_input);
        assert_eq!(escaped, "Hello 世界 🌍 &lt;test&gt;");
        
        // Test emoji in entities
        let emoji_entity = "&#x1F600;"; // 😀
        let unescaped = unescape_html(emoji_entity);
        assert_eq!(unescaped, "😀");
    }

    #[test]
    fn test_performance_regression() {
        // Basic performance regression test
        let large_input = "<b>".repeat(1000);
        let start = std::time::Instant::now();
        let _escaped = escape_html(&large_input);
        let duration = start.elapsed();
        
        // Should complete within reasonable time (adjust threshold as needed)
        assert!(duration.as_millis() < 100, "Escaping took too long: {:?}", duration);
    }
}
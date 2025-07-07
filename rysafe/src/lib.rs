//! A high-performance HTML/XML escaping library for Python, implemented in Rust.
//!
//! This library provides fast, memory-safe HTML and XML escaping and unescaping
//! functionality with full compatibility with Python's MarkupSafe library.
//!
//! # Features
//!
//! - Super-fast HTML/XML escaping and unescaping
//! - 100% API compatibility with MarkupSafe
//! - Python bindings via PyO3/maturin
//! - FastAPI integration support
//! - Robust Unicode and edge case handling
//! - Memory-safe Rust implementation
//!
//! # Usage
//!
//! ```rust
//! use rysafe::{escape_html, unescape_html};
//!
//! let escaped = escape_html("<script>alert('xss')</script>");
//! assert_eq!(escaped, "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;");
//!
//! let unescaped = unescape_html("&lt;b&gt;bold&lt;/b&gt;");
//! assert_eq!(unescaped, "<b>bold</b>");
//! ```

pub mod error;
pub mod escape;

#[cfg(feature = "python")]
pub mod python;

// Re-export main functions for convenience
pub use error::{EscapeError, EscapeResult};
pub use escape::{escape_html, escape_html_bytes, unescape_html, unescape_html_bytes};

#[cfg(feature = "python")]
pub use python::rysafe;

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Library name
pub const NAME: &str = env!("CARGO_PKG_NAME");

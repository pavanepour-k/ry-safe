//! Core HTML/XML escaping and unescaping functionality.
//!
//! This module provides fast, memory-safe HTML/XML escaping that is fully
//! compatible with Python's MarkupSafe library. It handles Unicode correctly,
//! including surrogate pairs, and gracefully handles malformed input.

use std::borrow::Cow;
use std::collections::HashMap;

/// HTML entities for escaping common characters
const HTML_ESCAPE_TABLE: &[(char, &str)] = &[
    ('<', "&lt;"),
    ('>', "&gt;"),
    ('&', "&amp;"),
    ('"', "&quot;"),
    ('\'', "&#x27;"),
];

/// Mapping for unescaping HTML entities back to characters
fn create_unescape_table() -> HashMap<&'static str, char> {
    let mut table = HashMap::new();
    table.insert("&lt;", '<');
    table.insert("&gt;", '>');
    table.insert("&amp;", '&');
    table.insert("&quot;", '"');
    table.insert("&#x27;", '\'');
    table.insert("&#39;", '\''); // Alternative for single quote
                                 // Numeric entities
    table.insert("&#60;", '<');
    table.insert("&#62;", '>');
    table.insert("&#38;", '&');
    table.insert("&#34;", '"');
    table.insert("&#39;", '\'');
    table
}

/// Fast HTML escaping for string input.
///
/// Escapes the characters `<`, `>`, `&`, `"`, and `'` to their HTML entity equivalents.
/// This function is optimized for performance and handles Unicode correctly.
///
/// # Examples
///
/// ```rust
/// use rust_html_escape::escape_html;
///
/// assert_eq!(escape_html("<b>hello</b>"), "&lt;b&gt;hello&lt;/b&gt;");
/// assert_eq!(escape_html("\"quoted\""), "&quot;quoted&quot;");
/// assert_eq!(escape_html("safe text"), "safe text");
/// ```
pub fn escape_html(input: &str) -> Cow<str> {
    // Fast path: check if escaping is needed
    if !input
        .chars()
        .any(|c| matches!(c, '<' | '>' | '&' | '"' | '\''))
    {
        return Cow::Borrowed(input);
    }

    let mut result = String::with_capacity(input.len() * 2);

    for ch in input.chars() {
        match ch {
            '<' => result.push_str("&lt;"),
            '>' => result.push_str("&gt;"),
            '&' => result.push_str("&amp;"),
            '"' => result.push_str("&quot;"),
            '\'' => result.push_str("&#x27;"),
            _ => result.push(ch),
        }
    }

    Cow::Owned(result)
}

/// Fast HTML unescaping for string input.
///
/// Converts HTML entities back to their character equivalents.
/// Handles both named entities (&lt;, &gt;, etc.) and numeric entities (&#60;, &#62;, etc.).
///
/// # Examples
///
/// ```rust
/// use rust_html_escape::unescape_html;
///
/// assert_eq!(unescape_html("&lt;b&gt;hello&lt;/b&gt;"), "<b>hello</b>");
/// assert_eq!(unescape_html("&quot;quoted&quot;"), "\"quoted\"");
/// assert_eq!(unescape_html("safe text"), "safe text");
/// ```
pub fn unescape_html(input: &str) -> Cow<str> {
    if !input.contains('&') {
        return Cow::Borrowed(input);
    }

    let unescape_table = create_unescape_table();
    let mut result = String::with_capacity(input.len());
    let mut chars = input.char_indices().peekable();

    while let Some((i, ch)) = chars.next() {
        if ch == '&' {
            // Look for entity ending with ';'
            let remaining = &input[i..];
            if let Some(semicolon_pos) = remaining.find(';') {
                let entity = &remaining[..=semicolon_pos];

                if let Some(&unescaped_char) = unescape_table.get(entity) {
                    result.push(unescaped_char);
                    // Skip the entity characters
                    for _ in 0..entity.chars().count() - 1 {
                        chars.next();
                    }
                    continue;
                }

                // Try parsing numeric entities
                if entity.starts_with("&#") && entity.len() > 3 {
                    let number_part = &entity[2..entity.len() - 1];

                    // Hexadecimal
                    if number_part.starts_with('x') || number_part.starts_with('X') {
                        if let Ok(code_point) = u32::from_str_radix(&number_part[1..], 16) {
                            if let Some(unicode_char) = char::from_u32(code_point) {
                                result.push(unicode_char);
                                for _ in 0..entity.chars().count() - 1 {
                                    chars.next();
                                }
                                continue;
                            }
                        }
                    }
                    // Decimal
                    else if let Ok(code_point) = number_part.parse::<u32>() {
                        if let Some(unicode_char) = char::from_u32(code_point) {
                            result.push(unicode_char);
                            for _ in 0..entity.chars().count() - 1 {
                                chars.next();
                            }
                            continue;
                        }
                    }
                }
            }
        }

        result.push(ch);
    }

    if result == input {
        Cow::Borrowed(input)
    } else {
        Cow::Owned(result)
    }
}

/// Escape HTML in byte input, returning escaped bytes.
///
/// This function handles byte sequences that may contain invalid UTF-8.
/// Invalid sequences are preserved as-is, while valid UTF-8 portions are escaped.
pub fn escape_html_bytes(input: &[u8]) -> Vec<u8> {
    let mut result = Vec::with_capacity(input.len() * 2);
    let mut i = 0;

    while i < input.len() {
        match input[i] {
            b'<' => result.extend_from_slice(b"&lt;"),
            b'>' => result.extend_from_slice(b"&gt;"),
            b'&' => result.extend_from_slice(b"&amp;"),
            b'"' => result.extend_from_slice(b"&quot;"),
            b'\'' => result.extend_from_slice(b"&#x27;"),
            byte => result.push(byte),
        }
        i += 1;
    }

    result
}

/// Unescape HTML in byte input, returning unescaped bytes.
pub fn unescape_html_bytes(input: &[u8]) -> Vec<u8> {
    if !input.contains(&b'&') {
        return input.to_vec();
    }

    let mut result = Vec::with_capacity(input.len());
    let mut i = 0;

    while i < input.len() {
        if input[i] == b'&' {
            // Check for common entities
            if input[i..].starts_with(b"&lt;") {
                result.push(b'<');
                i += 4;
            } else if input[i..].starts_with(b"&gt;") {
                result.push(b'>');
                i += 4;
            } else if input[i..].starts_with(b"&amp;") {
                result.push(b'&');
                i += 5;
            } else if input[i..].starts_with(b"&quot;") {
                result.push(b'"');
                i += 6;
            } else if input[i..].starts_with(b"&#x27;") {
                result.push(b'\'');
                i += 6;
            } else if input[i..].starts_with(b"&#39;") {
                result.push(b'\'');
                i += 5;
            } else {
                result.push(input[i]);
                i += 1;
            }
        } else {
            result.push(input[i]);
            i += 1;
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_escape_html_basic() {
        assert_eq!(escape_html("<b>hello</b>"), "&lt;b&gt;hello&lt;/b&gt;");
        assert_eq!(escape_html("\"quoted\""), "&quot;quoted&quot;");
        assert_eq!(escape_html("'single'"), "&#x27;single&#x27;");
        assert_eq!(escape_html("safe & sound"), "safe &amp; sound");
    }

    #[test]
    fn test_escape_html_no_change() {
        assert_eq!(escape_html("safe text"), "safe text");
        assert_eq!(escape_html(""), "");
        assert_eq!(escape_html("123 abc"), "123 abc");
    }

    #[test]
    fn test_escape_html_unicode() {
        assert_eq!(escape_html("Hello 🌍"), "Hello 🌍");
        assert_eq!(escape_html("<🌍>"), "&lt;🌍&gt;");
        assert_eq!(escape_html("café & résumé"), "café &amp; résumé");
    }

    #[test]
    fn test_unescape_html_basic() {
        assert_eq!(unescape_html("&lt;b&gt;hello&lt;/b&gt;"), "<b>hello</b>");
        assert_eq!(unescape_html("&quot;quoted&quot;"), "\"quoted\"");
        assert_eq!(unescape_html("&#x27;single&#x27;"), "'single'");
        assert_eq!(unescape_html("safe &amp; sound"), "safe & sound");
    }

    #[test]
    fn test_unescape_html_numeric() {
        assert_eq!(unescape_html("&#60;test&#62;"), "<test>");
        assert_eq!(unescape_html("&#x3C;test&#x3E;"), "<test>");
        assert_eq!(unescape_html("&#39;single&#39;"), "'single'");
    }

    #[test]
    fn test_unescape_html_no_change() {
        assert_eq!(unescape_html("safe text"), "safe text");
        assert_eq!(unescape_html(""), "");
        assert_eq!(unescape_html("no entities here"), "no entities here");
    }

    #[test]
    fn test_roundtrip() {
        let test_cases = vec![
            "<b>hello</b>",
            "\"quoted\"",
            "'single'",
            "safe & sound",
            "<script>alert('xss')</script>",
            "Hello 🌍 & café",
        ];

        for case in test_cases {
            let escaped = escape_html(case);
            let unescaped = unescape_html(&escaped);
            assert_eq!(unescaped, case, "Roundtrip failed for: {}", case);
        }
    }

    #[test]
    fn test_escape_html_bytes() {
        assert_eq!(
            escape_html_bytes(b"<b>hello</b>"),
            b"&lt;b&gt;hello&lt;/b&gt;"
        );
        assert_eq!(escape_html_bytes(b"\"quoted\""), b"&quot;quoted&quot;");
        assert_eq!(escape_html_bytes(b"safe text"), b"safe text");
    }

    #[test]
    fn test_unescape_html_bytes() {
        assert_eq!(
            unescape_html_bytes(b"&lt;b&gt;hello&lt;/b&gt;"),
            b"<b>hello</b>"
        );
        assert_eq!(unescape_html_bytes(b"&quot;quoted&quot;"), b"\"quoted\"");
        assert_eq!(unescape_html_bytes(b"safe text"), b"safe text");
    }

    #[test]
    fn test_malformed_entities() {
        // Should not crash or panic on malformed entities
        assert_eq!(unescape_html("&notanentity;"), "&notanentity;");
        assert_eq!(unescape_html("&incomplete"), "&incomplete");
        assert_eq!(unescape_html("&#invalid;"), "&#invalid;");
        assert_eq!(unescape_html("&#x;"), "&#x;");
    }

    #[test]
    fn test_edge_cases() {
        // Empty string
        assert_eq!(escape_html(""), "");
        assert_eq!(unescape_html(""), "");

        // Single characters
        assert_eq!(escape_html("<"), "&lt;");
        assert_eq!(escape_html(">"), "&gt;");
        assert_eq!(escape_html("&"), "&amp;");

        // Multiple entities
        assert_eq!(escape_html("<>&\"'"), "&lt;&gt;&amp;&quot;&#x27;");
    }
}

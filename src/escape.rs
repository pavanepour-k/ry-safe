//! Core HTML/XML escaping and unescaping functionality
//! 
//! This module provides high-performance HTML/XML escaping and unescaping functions
//! that are fully compatible with Python's MarkupSafe library.

use std::borrow::Cow;

/// HTML entities to escape
const HTML_ESCAPE_TABLE: &[(&str, &str)] = &[
    ("&", "&amp;"),   // Must be first to avoid double-escaping
    ("<", "&lt;"),
    (">", "&gt;"),
    ("\"", "&quot;"),
    ("'", "&#x27;"),  // &#39; also works, but &#x27; is more compatible
];

/// HTML entities to unescape
const HTML_UNESCAPE_TABLE: &[(&str, &str)] = &[
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&quot;", "\""),
    ("&#x27;", "'"),
    ("&#39;", "'"),   // Alternative single quote encoding
    ("&apos;", "'"),  // XML-style single quote
];

/// Escapes HTML/XML special characters in a string
/// 
/// This function replaces characters that have special meaning in HTML/XML
/// with their corresponding HTML entities, preventing XSS attacks and ensuring
/// proper rendering.
/// 
/// # Arguments
/// 
/// * `input` - The string to escape
/// 
/// # Returns
/// 
/// A string with HTML special characters escaped
/// 
/// # Examples
/// 
/// ```
/// use rust_html_escape::escape_html;
/// 
/// assert_eq!(escape_html("<b>Hello & \"World\"</b>"), 
///            "&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;");
/// ```
pub fn escape_html(input: &str) -> String {
    if input.is_empty() {
        return String::new();
    }

    // Quick check if escaping is needed
    if !input.chars().any(|c| matches!(c, '&' | '<' | '>' | '"' | '\'')) {
        return input.to_string();
    }

    let mut result = String::with_capacity(input.len() * 2); // Pre-allocate some extra space
    let mut last_end = 0;

    for (start, part) in input.match_indices(&['&', '<', '>', '"', '\''][..]) {
        // Add the unmatched portion
        result.push_str(&input[last_end..start]);
        
        // Add the escaped character
        match part {
            "&" => result.push_str("&amp;"),
            "<" => result.push_str("&lt;"),
            ">" => result.push_str("&gt;"),
            "\"" => result.push_str("&quot;"),
            "'" => result.push_str("&#x27;"),
            _ => unreachable!("match_indices should only return specified chars"),
        }
        
        last_end = start + part.len();
    }
    
    // Add any remaining unmatched portion
    result.push_str(&input[last_end..]);
    result
}

/// Unescapes HTML/XML entities in a string
/// 
/// This function converts HTML entities back to their original characters.
/// It handles the most common HTML entities including numeric character references.
/// 
/// # Arguments
/// 
/// * `input` - The string to unescape
/// 
/// # Returns
/// 
/// A string with HTML entities converted back to their original characters
/// 
/// # Examples
/// 
/// ```
/// use rust_html_escape::unescape_html;
/// 
/// assert_eq!(unescape_html("&lt;b&gt;Hello &amp; &quot;World&quot;&lt;/b&gt;"),
///            "<b>Hello & \"World\"</b>");
/// ```
pub fn unescape_html(input: &str) -> String {
    if input.is_empty() || !input.contains('&') {
        return input.to_string();
    }

    let mut result = String::with_capacity(input.len());
    let mut chars = input.chars().peekable();
    
    while let Some(ch) = chars.next() {
        if ch == '&' {
            // Look for entity end
            let mut entity = String::new();
            let mut found_semicolon = false;
            
            // Collect characters until semicolon or end (max 10 chars for safety)
            for _ in 0..10 {
                if let Some(&next_ch) = chars.peek() {
                    if next_ch == ';' {
                        chars.next(); // consume semicolon
                        found_semicolon = true;
                        break;
                    } else if next_ch.is_ascii_alphanumeric() || next_ch == '#' || next_ch == 'x' {
                        entity.push(chars.next().unwrap());
                    } else {
                        break; // Invalid entity character
                    }
                } else {
                    break; // End of input
                }
            }
            
            if found_semicolon {
                let full_entity = format!("&{};", entity);
                
                // Try to match standard entities first
                let mut matched = false;
                for (entity_name, replacement) in HTML_UNESCAPE_TABLE {
                    if full_entity == *entity_name {
                        result.push_str(replacement);
                        matched = true;
                        break;
                    }
                }
                
                if !matched {
                    // Try numeric character references
                    if let Some(decoded) = decode_numeric_entity(&entity) {
                        result.push(decoded);
                    } else {
                        // If we can't decode, keep the original
                        result.push('&');
                        result.push_str(&entity);
                        result.push(';');
                    }
                }
            } else {
                // No semicolon found, not a valid entity
                result.push('&');
                result.push_str(&entity);
            }
        } else {
            result.push(ch);
        }
    }
    
    result
}

/// Decodes numeric HTML character references (&#123; or &#x1A;)
fn decode_numeric_entity(entity: &str) -> Option<char> {
    if entity.starts_with('#') {
        let num_part = &entity[1..];
        
        if num_part.starts_with('x') || num_part.starts_with('X') {
            // Hexadecimal entity &#x1A;
            let hex_part = &num_part[1..];
            if let Ok(code_point) = u32::from_str_radix(hex_part, 16) {
                return char::from_u32(code_point);
            }
        } else {
            // Decimal entity &#123;
            if let Ok(code_point) = num_part.parse::<u32>() {
                return char::from_u32(code_point);
            }
        }
    }
    None
}

/// Escapes HTML but returns None for None input (MarkupSafe compatibility)
pub fn escape_silent(input: Option<&str>) -> Option<String> {
    input.map(escape_html)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_escape_basic() {
        assert_eq!(escape_html("hello"), "hello");
        assert_eq!(escape_html(""), "");
        assert_eq!(escape_html("<b>hello</b>"), "&lt;b&gt;hello&lt;/b&gt;");
    }

    #[test]
    fn test_escape_all_entities() {
        let input = "<>&\"'";
        let expected = "&lt;&gt;&amp;&quot;&#x27;";
        assert_eq!(escape_html(input), expected);
    }

    #[test]
    fn test_escape_mixed_content() {
        let input = "<script>alert('XSS & \"injection\"')</script>";
        let expected = "&lt;script&gt;alert(&#x27;XSS &amp; &quot;injection&quot;&#x27;)&lt;/script&gt;";
        assert_eq!(escape_html(input), expected);
    }

    #[test]
    fn test_unescape_basic() {
        assert_eq!(unescape_html("hello"), "hello");
        assert_eq!(unescape_html(""), "");
        assert_eq!(unescape_html("&lt;b&gt;hello&lt;/b&gt;"), "<b>hello</b>");
    }

    #[test]
    fn test_unescape_all_entities() {
        let input = "&lt;&gt;&amp;&quot;&#x27;";
        let expected = "<>&\"'";
        assert_eq!(unescape_html(input), expected);
    }

    #[test]
    fn test_unescape_numeric_entities() {
        assert_eq!(unescape_html("&#65;"), "A"); // Decimal
        assert_eq!(unescape_html("&#x41;"), "A"); // Hexadecimal
        assert_eq!(unescape_html("&#x1F600;"), "😀"); // Unicode emoji
    }

    #[test]
    fn test_escape_silent() {
        assert_eq!(escape_silent(Some("<b>test</b>")), Some("&lt;b&gt;test&lt;/b&gt;".to_string()));
        assert_eq!(escape_silent(None), None);
    }

    #[test]
    fn test_roundtrip() {
        let original = "<b>Hello & \"World\"</b>";
        let escaped = escape_html(original);
        let unescaped = unescape_html(&escaped);
        assert_eq!(original, unescaped);
    }

    #[test]
    fn test_unicode_handling() {
        let input = "Hello 世界 🌍";
        let escaped = escape_html(input);
        assert_eq!(escaped, input); // No escaping needed for these chars
        
        let with_entities = "Hello &lt;世界&gt; 🌍";
        let unescaped = unescape_html(with_entities);
        assert_eq!(unescaped, "Hello <世界> 🌍");
    }

    #[test]
    fn test_malformed_entities() {
        // Incomplete entities should be left as-is
        assert_eq!(unescape_html("&lt"), "&lt");
        assert_eq!(unescape_html("&invalid;"), "&invalid;");
        assert_eq!(unescape_html("&#999999999;"), "&#999999999;"); // Invalid code point
    }

    #[test]
    fn test_edge_cases() {
        // Empty string
        assert_eq!(escape_html(""), "");
        assert_eq!(unescape_html(""), "");
        
        // Only special chars
        assert_eq!(escape_html("&"), "&amp;");
        assert_eq!(unescape_html("&amp;"), "&");
        
        // No special chars
        assert_eq!(escape_html("hello world"), "hello world");
        assert_eq!(unescape_html("hello world"), "hello world");
    }

    #[test]
    fn test_performance_critical_paths() {
        // Test with larger strings to ensure performance
        let large_string = "a".repeat(1000);
        let escaped = escape_html(&large_string);
        assert_eq!(escaped, large_string); // No changes needed
        
        let large_with_entities = "&amp;".repeat(1000);
        let unescaped = unescape_html(&large_with_entities);
        assert_eq!(unescaped, "&".repeat(1000));
    }
}
use pyo3::prelude::*;
use std::collections::HashMap;

// Lazy static for entity lookup table
lazy_static::lazy_static! {
    static ref ENTITY_MAP: HashMap<&'static str, char> = {
        let mut m = HashMap::new();
        // Named entities
        m.insert("amp", '&');
        m.insert("lt", '<');
        m.insert("gt", '>');
        m.insert("quot", '"');
        m.insert("#x27", '\'');  // Keep for compatibility
        m.insert("apos", '\'');   // Standard XML entity

        // Common named entities
        m.insert("nbsp", '\u{00A0}');
        m.insert("copy", '\u{00A9}');
        m.insert("reg", '\u{00AE}');
        m.insert("trade", '\u{2122}');
        m.insert("euro", '\u{20AC}');
        m.insert("pound", '\u{00A3}');
        m.insert("yen", '\u{00A5}');
        m.insert("cent", '\u{00A2}');
        m.insert("sect", '\u{00A7}');
        m.insert("deg", '\u{00B0}');
        m.insert("plusmn", '\u{00B1}');
        m.insert("para", '\u{00B6}');
        m.insert("middot", '\u{00B7}');
        m.insert("frac14", '\u{00BC}');
        m.insert("frac12", '\u{00BD}');
        m.insert("frac34", '\u{00BE}');
        m.insert("iquest", '\u{00BF}');

        // Math symbols
        m.insert("times", '\u{00D7}');
        m.insert("divide", '\u{00F7}');
        m.insert("minus", '\u{2212}');

        // Arrows
        m.insert("larr", '\u{2190}');
        m.insert("uarr", '\u{2191}');
        m.insert("rarr", '\u{2192}');
        m.insert("darr", '\u{2193}');
        m.insert("harr", '\u{2194}');

        // Other common entities
        m.insert("bull", '\u{2022}');
        m.insert("hellip", '\u{2026}');
        m.insert("prime", '\u{2032}');
        m.insert("Prime", '\u{2033}');
        m.insert("lsaquo", '\u{2039}');
        m.insert("rsaquo", '\u{203A}');
        m.insert("oline", '\u{203E}');
        m.insert("frasl", '\u{2044}');

        m
    };
}

#[pyfunction]
#[pyo3(name = "unescape")]
pub fn unescape_fn(text: &str) -> PyResult<String> {
    if text.is_empty() || !text.contains('&') {
        return Ok(text.to_string());
    }

    let mut result = String::with_capacity(text.len());
    let mut chars = text.char_indices();

    while let Some((i, ch)) = chars.next() {
        if ch == '&' {
            let remaining = &text[i + 1..];

            if let Some((entity, skip_len)) = parse_entity(remaining) {
                result.push(entity);
                // Skip the parsed entity characters
                for _ in 0..skip_len {
                    chars.next();
                }
            } else {
                result.push(ch);
            }
        } else {
            result.push(ch);
        }
    }

    Ok(result)
}

fn parse_entity(text: &str) -> Option<(char, usize)> {
    // Find the end of the entity (semicolon or invalid character)
    let end_pos = text
        .find(|c: char| c == ';' || (!c.is_alphanumeric() && c != '#' && c != 'x' && c != 'X'))
        .unwrap_or(text.len());

    if end_pos == 0 {
        return None;
    }

    let entity_content = &text[..end_pos];
    let has_semicolon = text.chars().nth(end_pos) == Some(';');
    let skip_len = if has_semicolon { end_pos + 1 } else { end_pos };

    // Try numeric entity first
    if entity_content.starts_with('#') {
        if let Some(ch) = parse_numeric_entity(&entity_content[1..]) {
            return Some((ch, skip_len));
        }
    }

    // Try named entity
    if let Some(&ch) = ENTITY_MAP.get(entity_content) {
        return Some((ch, skip_len));
    }

    // For backward compatibility, also check numeric entities without #
    // (e.g., "38" for ampersand)
    if entity_content.chars().all(|c| c.is_ascii_digit()) {
        if let Ok(code) = entity_content.parse::<u32>() {
            if let Some(ch) = char::from_u32(code) {
                if is_valid_char(ch) {
                    return Some((ch, skip_len));
                }
            }
        }
    }

    None
}

fn parse_numeric_entity(text: &str) -> Option<char> {
    if text.is_empty() {
        return None;
    }

    let (radix, digits) = if text.starts_with('x') || text.starts_with('X') {
        (16, &text[1..])
    } else {
        (10, text)
    };

    // Validate digit length (prevent DoS with huge numbers)
    let max_len = if radix == 16 { 8 } else { 10 };
    if digits.is_empty() || digits.len() > max_len {
        return None;
    }

    // Parse the number
    let code = u32::from_str_radix(digits, radix).ok()?;

    // Convert to char and validate
    let ch = char::from_u32(code)?;

    if is_valid_char(ch) {
        Some(ch)
    } else {
        None
    }
}

fn is_valid_char(ch: char) -> bool {
    // Allow all non-control characters, plus tab, newline, and carriage return
    !ch.is_control() || ch == '\t' || ch == '\n' || ch == '\r'
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_unescape_basic() {
        assert_eq!(unescape_fn("").unwrap(), "");
        assert_eq!(unescape_fn("hello").unwrap(), "hello");
        assert_eq!(unescape_fn("&lt;&gt;&amp;&quot;&#x27;").unwrap(), "<>&\"'");
        assert_eq!(unescape_fn("&apos;").unwrap(), "'");
    }

    #[test]
    fn test_unescape_mixed() {
        assert_eq!(
            unescape_fn("Hello &lt;world&gt; &amp; &quot;friends&quot;").unwrap(),
            "Hello <world> & \"friends\""
        );
    }

    #[test]
    fn test_unescape_numeric() {
        assert_eq!(unescape_fn("&#60;&#62;&#38;").unwrap(), "<>&");
        assert_eq!(unescape_fn("&#x3C;&#x3E;&#x26;").unwrap(), "<>&");
        assert_eq!(unescape_fn("&#x3c;&#x3e;&#x26;").unwrap(), "<>&"); // lowercase x
    }

    #[test]
    fn test_unescape_without_semicolon() {
        // Should still work without semicolon if followed by non-entity char
        assert_eq!(unescape_fn("&lt &gt").unwrap(), "< >");
        assert_eq!(unescape_fn("&amp,test").unwrap(), "&,test");
    }

    #[test]
    fn test_unescape_common_entities() {
        assert_eq!(unescape_fn("&copy;").unwrap(), "©");
        assert_eq!(unescape_fn("&nbsp;").unwrap(), "\u{00A0}");
        assert_eq!(unescape_fn("&euro;").unwrap(), "€");
        assert_eq!(unescape_fn("&hellip;").unwrap(), "…");
    }

    #[test]
    fn test_unescape_invalid() {
        assert_eq!(unescape_fn("&invalid;").unwrap(), "&invalid;");
        assert_eq!(unescape_fn("& test").unwrap(), "& test");
        assert_eq!(unescape_fn("&#;").unwrap(), "&#;");
        assert_eq!(unescape_fn("&#x;").unwrap(), "&#x;");
    }

    #[test]
    fn test_unescape_control_chars() {
        // Control characters should not be unescaped (except tab, newline, CR)
        assert_eq!(unescape_fn("&#0;").unwrap(), "&#0;");
        assert_eq!(unescape_fn("&#31;").unwrap(), "&#31;");
        assert_eq!(unescape_fn("&#9;").unwrap(), "\t");
        assert_eq!(unescape_fn("&#10;").unwrap(), "\n");
        assert_eq!(unescape_fn("&#13;").unwrap(), "\r");
    }
}

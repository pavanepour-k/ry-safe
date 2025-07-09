use pyo3::prelude::*;

const ENTITY_MAP: [(&str, char); 5] = [
    ("&amp;", '&'),
    ("&lt;", '<'),
    ("&gt;", '>'),
    ("&quot;", '"'),
    ("&#x27;", '\''),
];

const NUMERIC_ENTITIES: [(&str, char); 5] = [
    ("&#38;", '&'),
    ("&#60;", '<'),
    ("&#62;", '>'),
    ("&#34;", '"'),
    ("&#39;", '\''),
];

#[pyfunction]
#[pyo3(name = "unescape")]
pub fn unescape_fn(text: &str) -> PyResult<String> {
    if text.is_empty() || !text.contains('&') {
        return Ok(text.to_string());
    }

    let mut result = String::with_capacity(text.len());
    let mut chars = text.chars();

    while let Some(ch) = chars.next() {
        if ch == '&' {
            let remaining: String = chars.clone().collect();
            let mut found = false;

            for (entity, replacement) in &ENTITY_MAP {
                if remaining.starts_with(&entity[1..]) {
                    result.push(*replacement);
                    for _ in 1..entity.len() {
                        chars.next();
                    }
                    found = true;
                    break;
                }
            }

            if !found {
                for (entity, replacement) in &NUMERIC_ENTITIES {
                    if remaining.starts_with(&entity[1..]) {
                        result.push(*replacement);
                        for _ in 1..entity.len() {
                            chars.next();
                        }
                        found = true;
                        break;
                    }
                }
            }

            if !found {
                if remaining.starts_with("#x") || remaining.starts_with("#X") {
                    if let Some((hex_str, _)) = parse_hex_entity(&remaining[2..]) {
                        if let Ok(code) = u32::from_str_radix(hex_str, 16) {
                            if let Some(unicode_char) = char::from_u32(code) {
                                if !unicode_char.is_control()
                                    || unicode_char == '\t'
                                    || unicode_char == '\n'
                                    || unicode_char == '\r'
                                {
                                    result.push(unicode_char);
                                    for _ in 0..(hex_str.len() + 3) {
                                        chars.next();
                                    }
                                    found = true;
                                }
                            }
                        }
                    }
                } else if remaining.starts_with('#') {
                    if let Some((dec_str, _)) = parse_dec_entity(&remaining[1..]) {
                        if let Ok(code) = dec_str.parse::<u32>() {
                            if let Some(unicode_char) = char::from_u32(code) {
                                if !unicode_char.is_control()
                                    || unicode_char == '\t'
                                    || unicode_char == '\n'
                                    || unicode_char == '\r'
                                {
                                    result.push(unicode_char);
                                    for _ in 0..(dec_str.len() + 2) {
                                        chars.next();
                                    }
                                    found = true;
                                }
                            }
                        }
                    }
                }
            }

            if !found {
                result.push(ch);
            }
        } else {
            result.push(ch);
        }
    }

    Ok(result)
}

fn parse_hex_entity(s: &str) -> Option<(&str, usize)> {
    let mut end = 0;
    for (i, ch) in s.chars().enumerate() {
        if ch == ';' {
            return Some((&s[..i], i + 1));
        }
        if !ch.is_ascii_hexdigit() {
            break;
        }
        end = i + 1;
        if end > 8 {
            break;
        }
    }
    if end > 0 {
        Some((&s[..end], end))
    } else {
        None
    }
}

fn parse_dec_entity(s: &str) -> Option<(&str, usize)> {
    let mut end = 0;
    for (i, ch) in s.chars().enumerate() {
        if ch == ';' {
            return Some((&s[..i], i + 1));
        }
        if !ch.is_ascii_digit() {
            break;
        }
        end = i + 1;
        if end > 10 {
            break;
        }
    }
    if end > 0 {
        Some((&s[..end], end))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_unescape_basic() {
        assert_eq!(unescape_fn("").unwrap(), "");
        assert_eq!(unescape_fn("hello").unwrap(), "hello");
        assert_eq!(unescape_fn("&lt;&gt;&amp;&quot;&#x27;").unwrap(), "<>&\"'");
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
    }

    #[test]
    fn test_unescape_invalid() {
        assert_eq!(unescape_fn("&invalid;").unwrap(), "&invalid;");
        assert_eq!(unescape_fn("& test").unwrap(), "&test");
    }
}

use std::borrow::Cow;

const ESCAPED_CHARS: [(char, &str); 5] = [
    ('&', "&amp;"),
    ('<', "&lt;"),
    ('>', "&gt;"),
    ('"', "&#34;"),
    ('\'', "&#39;"),
];

pub fn escape(text: &str) -> Cow<str> {
    let mut escaped = None;
    let mut last_end = 0;

    for (i, ch) in text.char_indices() {
        let replacement = match ch {
            '&' => "&amp;",
            '<' => "&lt;",
            '>' => "&gt;",
            '"' => "&#34;",
            '\'' => "&#39;",
            _ => continue,
        };

        if escaped.is_none() {
            let mut s = String::with_capacity(text.len() + 10);
            escaped = Some(s);
        }

        if let Some(ref mut s) = escaped {
            s.push_str(&text[last_end..i]);
            s.push_str(replacement);
            last_end = i + ch.len_utf8();
        }
    }

    match escaped {
        Some(mut s) => {
            s.push_str(&text[last_end..]);
            Cow::Owned(s)
        }
        None => Cow::Borrowed(text),
    }
}

pub fn escape_silent(text: Option<&str>) -> Cow<str> {
    match text {
        Some(t) => escape(t),
        None => Cow::Borrowed(""),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_escape_needed() {
        assert_eq!(escape("hello world"), "hello world");
        assert_eq!(escape(""), "");
        assert_eq!(escape("safe text 123"), "safe text 123");
    }

    #[test]
    fn test_escape_all_chars() {
        assert_eq!(escape("&<>\"'"), "&amp;&lt;&gt;&#34;&#39;");
    }

    #[test]
    fn test_escape_mixed() {
        assert_eq!(
            escape("Hello <world> & \"friends\""),
            "Hello &lt;world&gt; &amp; &#34;friends&#34;"
        );
    }

    #[test]
    fn test_escape_silent() {
        assert_eq!(escape_silent(Some("test")), "test");
        assert_eq!(escape_silent(None), "");
        assert_eq!(escape_silent(Some("<test>")), "&lt;test&gt;");
    }

    #[test]
    fn test_unicode() {
        assert_eq!(escape("Hello 世界 <test>"), "Hello 世界 &lt;test&gt;");
        assert_eq!(escape("emoji 😀 & text"), "emoji 😀 &amp; text");
    }
}

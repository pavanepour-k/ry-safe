use markupsafe_rust::core::{escape, escape_silent};
use proptest::prelude::*;

#[test]
fn test_empty_string() {
    assert_eq!(escape(""), "");
}

#[test]
fn test_single_chars() {
    assert_eq!(escape("&"), "&amp;");
    assert_eq!(escape("<"), "&lt;");
    assert_eq!(escape(">"), "&gt;");
    assert_eq!(escape("\""), "&#34;");
    assert_eq!(escape("'"), "&#39;");
}

#[test]
fn test_consecutive_escapes() {
    assert_eq!(escape("<<>>"), "&lt;&lt;&gt;&gt;");
    assert_eq!(escape("&&&&"), "&amp;&amp;&amp;&amp;");
}

#[test]
fn test_escape_at_boundaries() {
    assert_eq!(escape("<start"), "&lt;start");
    assert_eq!(escape("end>"), "end&gt;");
    assert_eq!(escape("<middle>"), "&lt;middle&gt;");
}

#[test]
fn test_mixed_utf8() {
    assert_eq!(escape("日本語<test>中文"), "日本語&lt;test&gt;中文");
    assert_eq!(escape("🔥<fire>&🔥"), "🔥&lt;fire&gt;&amp;🔥");
}

#[test]
fn test_escape_silent_variants() {
    assert_eq!(escape_silent(None), "");
    assert_eq!(escape_silent(Some("")), "");
    assert_eq!(escape_silent(Some("normal")), "normal");
    assert_eq!(escape_silent(Some("<tag>")), "&lt;tag&gt;");
}

#[test]
fn test_real_world_html() {
    let input = r#"<script>alert("XSS")</script>"#;
    let expected = r#"&lt;script&gt;alert(&#34;XSS&#34;)&lt;/script&gt;"#;
    assert_eq!(escape(input), expected);
}

#[test]
fn test_attribute_injection() {
    let input = r#"onclick="alert('xss')""#;
    let expected = r#"onclick=&#34;alert(&#39;xss&#39;)&#34;"#;
    assert_eq!(escape(input), expected);
}

proptest! {
    #[test]
    fn test_escape_idempotent(s: String) {
        let once = escape(&s);
        let twice = escape(&once);
        prop_assert_eq!(&once, &twice);
    }

    #[test]
    fn test_escape_preserves_safe_chars(s in "[a-zA-Z0-9 ]+") {
        prop_assert_eq!(escape(&s).as_ref(), &s);
    }

    #[test]
    fn test_escape_length_increases(s: String) {
        let escaped = escape(&s);
        prop_assert!(escaped.len() >= s.len());
    }

    #[test]
    fn test_no_raw_special_chars(s: String) {
        let escaped = escape(&s);
        prop_assert!(!escaped.contains('<') || s.contains('<'));
        prop_assert!(!escaped.contains('>') || s.contains('>'));
        prop_assert!(!escaped.contains('&') || escaped.contains("&amp;"));
        prop_assert!(!escaped.contains('"') || s.contains('"'));
        prop_assert!(!escaped.contains('\'') || s.contains('\''));
    }
}

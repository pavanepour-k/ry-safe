//! Comprehensive Rust tests for rysafe core functionality.
//!
//! This test suite covers core logic, error handling, edge cases, and security
//! scenarios to ensure robust operation across all inputs.

use rysafe::{escape_html, escape_html_bytes, unescape_html, unescape_html_bytes};
use rysafe::{EscapeError, EscapeResult};

#[cfg(test)]
mod core_functionality_tests {
    use super::*;

    #[test]
    fn test_basic_html_escaping() {
        assert_eq!(escape_html("<b>hello</b>"), "&lt;b&gt;hello&lt;/b&gt;");
        assert_eq!(escape_html("\"quoted\""), "&quot;quoted&quot;");
        assert_eq!(escape_html("'single'"), "&#x27;single&#x27;");
        assert_eq!(escape_html("safe & sound"), "safe &amp; sound");
        assert_eq!(escape_html("<>&\"'"), "&lt;&gt;&amp;&quot;&#x27;");
    }

    #[test]
    fn test_basic_html_unescaping() {
        assert_eq!(unescape_html("&lt;b&gt;hello&lt;/b&gt;"), "<b>hello</b>");
        assert_eq!(unescape_html("&quot;quoted&quot;"), "\"quoted\"");
        assert_eq!(unescape_html("&#x27;single&#x27;"), "'single'");
        assert_eq!(unescape_html("&#39;single&#39;"), "'single'");
        assert_eq!(unescape_html("safe &amp; sound"), "safe & sound");
    }

    #[test]
    fn test_no_escaping_needed() {
        let safe_strings = vec![
            "safe text",
            "hello world",
            "",
            "123 abc",
            "unicode: café résumé 🌍",
        ];

        for s in safe_strings {
            assert_eq!(escape_html(s), s);
            assert_eq!(unescape_html(s), s);
        }
    }

    #[test]
    fn test_roundtrip_consistency() {
        let test_cases = vec![
            "<b>hello</b>",
            "\"quoted string\"",
            "'single quoted'",
            "mixed <b>\"quotes\"</b> & symbols",
            "<script>alert('xss')</script>",
            "Hello 🌍 & café résumé",
            "&existing; entities &amp; new",
            "",
            "<>&\"'",
        ];

        for case in test_cases {
            let escaped = escape_html(case);
            let unescaped = unescape_html(&escaped);
            assert_eq!(unescaped, case, "Roundtrip failed for: {}", case);
        }
    }
}

#[cfg(test)]
mod unicode_and_encoding_tests {
    use super::*;

    #[test]
    fn test_unicode_handling() {
        // Basic Unicode
        assert_eq!(escape_html("café & résumé"), "café &amp; résumé");
        assert_eq!(unescape_html("café &amp; résumé"), "café & résumé");

        // Emoji
        assert_eq!(escape_html("Hello 🌍 <world>"), "Hello 🌍 &lt;world&gt;");
        assert_eq!(unescape_html("Hello 🌍 &lt;world&gt;"), "Hello 🌍 <world>");

        // Mixed scripts
        let mixed = "English 中文 العربية русский <tag>";
        let escaped = escape_html(mixed);
        let unescaped = unescape_html(&escaped);
        assert_eq!(unescaped, mixed);
    }

    #[test]
    fn test_numeric_entities() {
        assert_eq!(unescape_html("&#60;"), "<");
        assert_eq!(unescape_html("&#62;"), ">");
        assert_eq!(unescape_html("&#38;"), "&");
        assert_eq!(unescape_html("&#34;"), "\"");
        assert_eq!(unescape_html("&#39;"), "'");

        // Hexadecimal entities
        assert_eq!(unescape_html("&#x3C;"), "<");
        assert_eq!(unescape_html("&#x3E;"), ">");
        assert_eq!(unescape_html("&#x26;"), "&");
        assert_eq!(unescape_html("&#x22;"), "\"");
        assert_eq!(unescape_html("&#x27;"), "'");

        // Unicode code points
        assert_eq!(unescape_html("&#8364;"), "€"); // Euro sign
        assert_eq!(unescape_html("&#x1F30D;"), "🌍"); // Earth emoji
    }

    #[test]
    fn test_bytes_handling() {
        assert_eq!(
            escape_html_bytes(b"<b>hello</b>"),
            b"&lt;b&gt;hello&lt;/b&gt;"
        );
        assert_eq!(escape_html_bytes(b"\"quoted\""), b"&quot;quoted&quot;");
        assert_eq!(escape_html_bytes(b"safe text"), b"safe text");

        assert_eq!(
            unescape_html_bytes(b"&lt;b&gt;hello&lt;/b&gt;"),
            b"<b>hello</b>"
        );
        assert_eq!(unescape_html_bytes(b"&quot;quoted&quot;"), b"\"quoted\"");
        assert_eq!(unescape_html_bytes(b"safe text"), b"safe text");
    }
}

#[cfg(test)]
mod edge_cases_and_malformed_input_tests {
    use super::*;

    #[test]
    fn test_malformed_entities() {
        // Should not crash or panic on malformed entities
        let malformed_cases = vec![
            "&notanentity;",
            "&incomplete",
            "&#invalid;",
            "&#x;",
            "&#xGG;",
            "&amp",                   // Missing semicolon
            "&#999999999999999999;",  // Huge number
            "&#x999999999999999999;", // Huge hex number
        ];

        for case in malformed_cases {
            let result = unescape_html(case);
            // Should not crash and should return something reasonable
            assert!(!result.is_empty() || case.is_empty());
        }
    }

    #[test]
    fn test_empty_inputs() {
        assert_eq!(escape_html(""), "");
        assert_eq!(unescape_html(""), "");
        assert_eq!(escape_html_bytes(b""), b"");
        assert_eq!(unescape_html_bytes(b""), b"");
    }

    #[test]
    fn test_single_character_inputs() {
        let chars = vec!['<', '>', '&', '"', '\'', 'a', '1', ' '];

        for ch in chars {
            let input = ch.to_string();
            let escaped = escape_html(&input);
            let unescaped = unescape_html(&escaped);
            assert_eq!(unescaped, input, "Single char roundtrip failed for: {}", ch);
        }
    }

    #[test]
    fn test_large_inputs() {
        // Test with large strings
        let large_safe = "a".repeat(10000);
        assert_eq!(escape_html(&large_safe), large_safe);
        assert_eq!(unescape_html(&large_safe), large_safe);

        let large_unsafe = "<script>".repeat(1000);
        let escaped_large = escape_html(&large_unsafe);
        let unescaped_large = unescape_html(&escaped_large);
        assert_eq!(unescaped_large, large_unsafe);
    }

    #[test]
    fn test_nested_entities() {
        // Test already escaped content
        let already_escaped = "&lt;b&gt;hello&lt;/b&gt;";
        let double_escaped = escape_html(already_escaped);
        assert_eq!(double_escaped, "&amp;lt;b&amp;gt;hello&amp;lt;/b&amp;gt;");

        let unescaped_once = unescape_html(&double_escaped);
        assert_eq!(unescaped_once, already_escaped);

        let unescaped_twice = unescape_html(&unescaped_once);
        assert_eq!(unescaped_twice, "<b>hello</b>");
    }
}

#[cfg(test)]
mod security_tests {
    use super::*;

    #[test]
    fn test_xss_prevention() {
        let xss_payloads = vec![
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src=javascript:alert('xss')>",
            "<object data=javascript:alert('xss')>",
            "<embed src=javascript:alert('xss')>",
            "<link rel=stylesheet href=javascript:alert('xss')>",
            "<style>@import 'javascript:alert(\"xss\")'</style>",
            "<meta http-equiv=refresh content=0;url=javascript:alert('xss')>",
        ];

        for payload in xss_payloads {
            let escaped = escape_html(payload);
            // Ensure no unescaped < or > remain
            assert!(!escaped.contains('<'), "Unescaped < found in: {}", escaped);
            assert!(!escaped.contains('>'), "Unescaped > found in: {}", escaped);

            // Ensure roundtrip consistency
            let unescaped = unescape_html(&escaped);
            assert_eq!(unescaped, payload, "XSS roundtrip failed for: {}", payload);
        }
    }

    #[test]
    fn test_html_injection_prevention() {
        let injection_attempts = vec![
            "<script src='evil.js'></script>",
            "<div onclick='malicious()'>click me</div>",
            "<input type='text' value='\"onmouseover=\"alert('xss')\"'>",
            "<a href='javascript:void(0)' onclick='alert()'>link</a>",
            "<form action='javascript:alert()'>",
            "<meta charset='utf-8'>",
            "<!-- <script>alert()</script> -->",
        ];

        for injection in injection_attempts {
            let escaped = escape_html(injection);
            // Verify that dangerous characters are escaped
            assert!(!escaped.contains('<'), "Contains unescaped <: {}", escaped);
            assert!(!escaped.contains('>'), "Contains unescaped >: {}", escaped);
            assert!(
                !escaped.contains("javascript:"),
                "Contains unescaped javascript: {}",
                escaped
            );
        }
    }

    #[test]
    fn test_attribute_injection_prevention() {
        let attr_injections = vec![
            "value=\">alert('xss')<input type=\"",
            "title='onclick=alert() '",
            "data-value='\"><script>alert()</script>'",
            "class=\"foo\" onload=\"alert()\"",
        ];

        for injection in attr_injections {
            let escaped = escape_html(injection);
            assert!(
                !escaped.contains('"'),
                "Contains unescaped quote: {}",
                escaped
            );
            assert!(
                !escaped.contains('\''),
                "Contains unescaped single quote: {}",
                escaped
            );
            assert!(!escaped.contains('<'), "Contains unescaped <: {}", escaped);
            assert!(!escaped.contains('>'), "Contains unescaped >: {}", escaped);
        }
    }
}

#[cfg(test)]
mod performance_tests {
    use super::*;
    use std::time::Instant;

    #[test]
    fn test_performance_no_escaping_needed() {
        let safe_text = "This is a safe string with no special characters".repeat(100);
        let start = Instant::now();

        for _ in 0..1000 {
            let _result = escape_html(&safe_text);
        }

        let duration = start.elapsed();
        println!("Performance test (no escaping): {:?}", duration);
        // Should be very fast since no escaping is needed
        assert!(duration.as_millis() < 100);
    }

    #[test]
    fn test_performance_heavy_escaping() {
        let unsafe_text = "<script>&\"'</script>".repeat(100);
        let start = Instant::now();

        for _ in 0..1000 {
            let _result = escape_html(&unsafe_text);
        }

        let duration = start.elapsed();
        println!("Performance test (heavy escaping): {:?}", duration);
        // Should still be reasonably fast even with heavy escaping
        assert!(duration.as_millis() < 1000);
    }
}

#[cfg(test)]
mod compatibility_tests {
    use super::*;

    #[test]
    fn test_markupsafe_compatibility() {
        // Test cases that should match MarkupSafe behavior exactly
        let test_cases = vec![
            ("<", "&lt;"),
            (">", "&gt;"),
            ("&", "&amp;"),
            ("\"", "&quot;"),
            ("'", "&#x27;"), // MarkupSafe uses &#x27; for single quotes
            ("<script>", "&lt;script&gt;"),
            ("R&D", "R&amp;D"),
            ("\"Hello World\"", "&quot;Hello World&quot;"),
            ("'Hello World'", "&#x27;Hello World&#x27;"),
        ];

        for (input, expected) in test_cases {
            assert_eq!(
                escape_html(input),
                expected,
                "MarkupSafe compatibility failed for: {}",
                input
            );
        }
    }

    #[test]
    fn test_unescape_compatibility() {
        let test_cases = vec![
            ("&lt;", "<"),
            ("&gt;", ">"),
            ("&amp;", "&"),
            ("&quot;", "\""),
            ("&#x27;", "'"),
            ("&#39;", "'"),  // Alternative single quote representation
            ("&#60;", "<"),  // Numeric entity
            ("&#x3C;", "<"), // Hex entity
        ];

        for (input, expected) in test_cases {
            assert_eq!(
                unescape_html(input),
                expected,
                "Unescape compatibility failed for: {}",
                input
            );
        }
    }
}

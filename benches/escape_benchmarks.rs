//! Benchmarks for rysafe performance testing.
//!
//! This benchmark suite measures performance across different scenarios
//! to ensure optimal performance and detect regressions.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use rysafe::{escape_html, escape_html_bytes, unescape_html, unescape_html_bytes};

/// Benchmark basic HTML escaping performance
fn bench_escape_basic(c: &mut Criterion) {
    let mut group = c.benchmark_group("escape_basic");

    let test_cases = vec![
        (
            "no_escape",
            "This is a safe string with no special characters",
        ),
        ("light_escape", "This has <some> tags & entities"),
        ("heavy_escape", "<script>alert('xss');</script>"),
        (
            "mixed_content",
            "Normal text with <b>bold</b> and \"quotes\" & entities",
        ),
    ];

    for (name, input) in test_cases {
        group.bench_with_input(BenchmarkId::new("escape_html", name), &input, |b, input| {
            b.iter(|| escape_html(black_box(input)))
        });
    }

    group.finish();
}

/// Benchmark HTML unescaping performance
fn bench_unescape_basic(c: &mut Criterion) {
    let mut group = c.benchmark_group("unescape_basic");

    let test_cases = vec![
        ("no_unescape", "This is a safe string with no entities"),
        (
            "light_unescape",
            "This has &lt;some&gt; tags &amp; entities",
        ),
        (
            "heavy_unescape",
            "&lt;script&gt;alert(&#x27;xss&#x27;);&lt;/script&gt;",
        ),
        (
            "mixed_content",
            "Normal text with &lt;b&gt;bold&lt;/b&gt; and &quot;quotes&quot; &amp; entities",
        ),
    ];

    for (name, input) in test_cases {
        group.bench_with_input(
            BenchmarkId::new("unescape_html", name),
            &input,
            |b, input| b.iter(|| unescape_html(black_box(input))),
        );
    }

    group.finish();
}

/// Benchmark with different input sizes
fn bench_escape_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("escape_sizes");

    let base_safe = "This is a safe string with no special characters. ";
    let base_unsafe = "This has <script>alert('xss')</script> dangerous content. ";

    let sizes = vec![10, 100, 1000, 10000];

    for size in sizes {
        // Safe content (no escaping needed)
        let safe_content = base_safe.repeat(size);
        group.bench_with_input(
            BenchmarkId::new("safe_content", size),
            &safe_content,
            |b, input| b.iter(|| escape_html(black_box(input))),
        );

        // Unsafe content (escaping needed)
        let unsafe_content = base_unsafe.repeat(size);
        group.bench_with_input(
            BenchmarkId::new("unsafe_content", size),
            &unsafe_content,
            |b, input| b.iter(|| escape_html(black_box(input))),
        );
    }

    group.finish();
}

/// Benchmark bytes vs string performance
fn bench_bytes_vs_string(c: &mut Criterion) {
    let mut group = c.benchmark_group("bytes_vs_string");

    let test_string = "<script>alert('xss');</script>".repeat(100);
    let test_bytes = test_string.as_bytes();

    group.bench_function("escape_string", |b| {
        b.iter(|| escape_html(black_box(&test_string)))
    });

    group.bench_function("escape_bytes", |b| {
        b.iter(|| escape_html_bytes(black_box(test_bytes)))
    });

    let escaped_string = escape_html(&test_string);
    let escaped_bytes = escape_html_bytes(test_bytes);

    group.bench_function("unescape_string", |b| {
        b.iter(|| unescape_html(black_box(&escaped_string)))
    });

    group.bench_function("unescape_bytes", |b| {
        b.iter(|| unescape_html_bytes(black_box(&escaped_bytes)))
    });

    group.finish();
}

/// Benchmark roundtrip performance (escape -> unescape)
fn bench_roundtrip(c: &mut Criterion) {
    let mut group = c.benchmark_group("roundtrip");

    let test_cases = vec![
        ("simple", "<b>hello</b>"),
        ("complex", "<script>alert('xss & injection');</script>"),
        ("mixed", "Normal text with <tags> and \"quotes\" & entities"),
        ("large", "<div class=\"test\">content</div>".repeat(100)),
    ];

    for (name, input) in test_cases {
        group.bench_with_input(
            BenchmarkId::new("escape_unescape", name),
            &input,
            |b, input| {
                b.iter(|| {
                    let escaped = escape_html(black_box(input));
                    let _unescaped = unescape_html(black_box(&escaped));
                })
            },
        );
    }

    group.finish();
}

/// Benchmark Unicode handling performance
fn bench_unicode(c: &mut Criterion) {
    let mut group = c.benchmark_group("unicode");

    let test_cases = vec![
        ("ascii", "This is plain ASCII text with <tags>."),
        ("latin", "Café & résumé with <tags> français."),
        ("emoji", "Hello 🌍 <world> 🚀 & rockets!"),
        ("mixed_scripts", "English 中文 العربية русский <script>"),
        ("surrogate_pairs", "𝕳𝖊𝖑𝖑𝖔 🌟 <tag> 𝖜𝖔𝖗𝖑𝖉!"),
    ];

    for (name, input) in test_cases {
        group.bench_with_input(
            BenchmarkId::new("escape_unicode", name),
            &input,
            |b, input| b.iter(|| escape_html(black_box(input))),
        );

        let escaped = escape_html(input);
        group.bench_with_input(
            BenchmarkId::new("unescape_unicode", name),
            &escaped,
            |b, input| b.iter(|| unescape_html(black_box(input))),
        );
    }

    group.finish();
}

/// Benchmark numeric entity handling
fn bench_numeric_entities(c: &mut Criterion) {
    let mut group = c.benchmark_group("numeric_entities");

    let test_cases = vec![
        ("decimal_basic", "&#60;&#62;&#38;&#34;&#39;"),
        ("hex_basic", "&#x3C;&#x3E;&#x26;&#x22;&#x27;"),
        ("decimal_unicode", "&#8364;&#8482;&#169;&#174;"), // €™©®
        ("hex_unicode", "&#x20AC;&#x2122;&#xA9;&#xAE;"),   // €™©®
        ("mixed_entities", "&lt;&#60;&#x3C; test &gt;&#62;&#x3E;"),
        ("large_numbers", "&#127757;&#x1F30D;"), // 🌍 emoji
    ];

    for (name, input) in test_cases {
        group.bench_with_input(
            BenchmarkId::new("unescape_numeric", name),
            &input,
            |b, input| b.iter(|| unescape_html(black_box(input))),
        );
    }

    group.finish();
}

/// Benchmark malformed input handling
fn bench_malformed_input(c: &mut Criterion) {
    let mut group = c.benchmark_group("malformed_input");

    let test_cases = vec![
        ("incomplete_entities", "&amp &lt &gt &quot"),
        ("invalid_entities", "&notreal; &fake123; &"),
        ("broken_numeric", "&#invalid; &#x; &#xGGG;"),
        (
            "mixed_malformed",
            "Valid &amp; invalid &notreal; &#bad; content",
        ),
        ("many_ampersands", "&".repeat(1000)),
    ];

    for (name, input) in test_cases {
        group.bench_with_input(
            BenchmarkId::new("unescape_malformed", name),
            &input,
            |b, input| b.iter(|| unescape_html(black_box(input))),
        );
    }

    group.finish();
}

/// Benchmark worst-case scenarios
fn bench_worst_cases(c: &mut Criterion) {
    let mut group = c.benchmark_group("worst_cases");

    // Alternating safe and unsafe characters
    let alternating = (0..1000)
        .map(|i| if i % 2 == 0 { "<" } else { "safe" })
        .collect::<Vec<_>>()
        .join("");

    group.bench_function("alternating_escape", |b| {
        b.iter(|| escape_html(black_box(&alternating)))
    });

    // Every character needs escaping
    let all_unsafe = "<>&\"'".repeat(200);
    group.bench_function("all_unsafe", |b| {
        b.iter(|| escape_html(black_box(&all_unsafe)))
    });

    // Long entity sequences
    let long_entities = "&lt;&gt;&amp;&quot;&#x27;".repeat(200);
    group.bench_function("long_entities", |b| {
        b.iter(|| unescape_html(black_box(&long_entities)))
    });

    // Mixed content with high density of entities
    let mixed_dense = "text&lt;tag&gt;more&amp;content&quot;quoted&quot;".repeat(100);
    group.bench_function("dense_entities", |b| {
        b.iter(|| unescape_html(black_box(&mixed_dense)))
    });

    group.finish();
}

/// Benchmark comparison scenarios (to measure against other implementations)
fn bench_comparison_scenarios(c: &mut Criterion) {
    let mut group = c.benchmark_group("comparison");

    // Common web content patterns
    let html_document = r#"
    <!DOCTYPE html>
    <html>
    <head><title>Test & Example</title></head>
    <body>
        <h1>Hello "World" & Everyone</h1>
        <p>This is a <strong>test</strong> document.</p>
        <script>alert('This should be escaped');</script>
    </body>
    </html>
    "#
    .repeat(10);

    group.bench_function("html_document", |b| {
        b.iter(|| escape_html(black_box(&html_document)))
    });

    // JSON-like content
    let json_content =
        r#"{"name": "<script>alert('xss')</script>", "value": "safe & sound"}"#.repeat(50);
    group.bench_function("json_content", |b| {
        b.iter(|| escape_html(black_box(&json_content)))
    });

    // User comment-like content
    let user_content = "Great article! <3 I love it & want more. Check out my site: <a href='javascript:alert()'>click</a>".repeat(20);
    group.bench_function("user_content", |b| {
        b.iter(|| escape_html(black_box(&user_content)))
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_escape_basic,
    bench_unescape_basic,
    bench_escape_sizes,
    bench_bytes_vs_string,
    bench_roundtrip,
    bench_unicode,
    bench_numeric_entities,
    bench_malformed_input,
    bench_worst_cases,
    bench_comparison_scenarios
);
criterion_main!(benches);
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use markupsafe_rust::core::escape;

fn bench_no_escape(c: &mut Criterion) {
    let text = "This is a simple text without any special characters that need escaping.";
    c.bench_function("escape_no_special_chars", |b| {
        b.iter(|| escape(black_box(text)))
    });
}

fn bench_all_escape(c: &mut Criterion) {
    let text = "&<>\"'&<>\"'&<>\"'&<>\"'";
    c.bench_function("escape_all_special_chars", |b| {
        b.iter(|| escape(black_box(text)))
    });
}

fn bench_mixed_content(c: &mut Criterion) {
    let text = "Normal text with <some> HTML & \"quotes\" mixed in. It's a typical scenario.";
    c.bench_function("escape_mixed_content", |b| {
        b.iter(|| escape(black_box(text)))
    });
}

fn bench_long_text_no_escape(c: &mut Criterion) {
    let text = "Lorem ipsum ".repeat(100);
    c.bench_function("escape_long_no_special", |b| {
        b.iter(|| escape(black_box(&text)))
    });
}

fn bench_long_text_with_escape(c: &mut Criterion) {
    let base = "Lorem <ipsum> dolor & sit \"amet\", consectetur adipiscing elit. ";
    let text = base.repeat(50);
    c.bench_function("escape_long_with_special", |b| {
        b.iter(|| escape(black_box(&text)))
    });
}

fn bench_unicode(c: &mut Criterion) {
    let text = "Hello 世界 <script>alert('XSS')</script> & more 日本語";
    c.bench_function("escape_unicode", |b| b.iter(|| escape(black_box(text))));
}

criterion_group!(
    benches,
    bench_no_escape,
    bench_all_escape,
    bench_mixed_content,
    bench_long_text_no_escape,
    bench_long_text_with_escape,
    bench_unicode
);
criterion_main!(benches);

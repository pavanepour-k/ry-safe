# rysafe

High-performance HTML/XML escaping library for Python, implemented in Rust.

## Installation

```bash
pip install rysafe
```

## Development

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements-dev.txt

# Build
maturin develop

# Test
pytest
cargo test

# Benchmark
cargo bench
```
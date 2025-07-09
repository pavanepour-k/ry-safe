# rysafe

High-performance HTML/XML escaping library with Rust core and Python bindings.

[![CI](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml/badge.svg)](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Drop-in replacement for MarkupSafe
- Rust performance with PyO3 bindings
- Python 3.8-3.13 support
- FastAPI auto-escaping middleware
- Full HTML entity support
- Unicode handling

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check style
flake8 src/ --max-line-length=79
mypy src/

# Build
maturin develop
```

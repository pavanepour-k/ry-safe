# rysafe

Fast HTML/XML escaping library - drop-in replacement for MarkupSafe with Rust performance.



[![CI](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml/badge.svg)](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/pavanepour-k/rysafe/branch/main/graph/badge.svg)](https://codecov.io/gh/pavanepour-k/rysafe)

## Features

- ✅ **Super-fast** HTML/XML escaping and unescaping, implemented in Rust
- ✅ **Security-first** with robust XSS protection and input validation
- ✅ **Drop-in replacement** for MarkupSafe with 100% API compatibility
- ✅ **FastAPI ready** with dependency injection and middleware support
- ✅ **Unicode-safe** handling of all character encodings and edge cases
- ✅ **Thoroughly tested** with comprehensive test coverage (Rust + Python)
- ✅ **Easy installation** via pip with pre-built wheels for all platforms
- ⚠️ **Minimal dependencies** - uses html-escape crate for robust escaping

## Installation

```bash
pip install rysafe
```

## Usage

```python
from rysafe import escape, Markup

# Basic escaping
print(escape('<script>alert(1)</script>'))  # &lt;script&gt;alert(1)&lt;/script&gt;

# Unicode support
print(escape('Hello 世界 & <Friends>'))  # Hello 世界 &amp; &lt;Friends&gt;

# Create safe markup
markup = Markup('<b>Bold text</b>')
print(markup + ' <unsafe>')  # <b>Bold text</b> &lt;unsafe&gt;

# Format strings safely
template = Markup('<p>Hello %s</p>')
print(template % 'World & Friends')  # <p>Hello World &amp; Friends</p>
```

## API Compatibility

rysafe provides 100% API compatibility with MarkupSafe:

- `escape(s)` - Escape special characters
- `escape_silent(s)` - Escape but return empty string for None
- `soft_str(s)` - Convert to string without escaping if already Markup
- `Markup` class - String subclass that marks content as safe

## FastAPI Integration

### Basic Usage
```python
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import rysafe

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Register escape and Markup in template globals
templates.env.globals['escape'] = rysafe.escape
templates.env.globals['Markup'] = rysafe.Markup
```

### With Middleware
```python
from fastapi_middleware import setup_rysafe

app = FastAPI()
setup_rysafe(app)  # Automatically injects rysafe into request state
```

## Performance

rysafe uses Rust's html-escape crate for 5-10x faster escaping compared to pure Python implementations.

## Requirements

- Python ≥ 3.9
- Works with all major web frameworks (FastAPI, Flask, Django)

## Development

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=rysafe
cargo test

# Build package
maturin develop
```
# rysafe

High-performance HTML/XML escaping library with Rust core and Python bindings.

[![CI (core-init)](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml/badge.svg?branch=core-init)](https://github.com/pavanepour-k/rysafe/actions/workflows/ci.yml?branch=core-init)
[![Python Version](https://img.shields.io/pypi/pyversions/rysafe.svg)](https://pypi.org/project/rysafe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Drop-in replacement for MarkupSafe
- Rust performance with PyO3 bindings
- Python 3.8-3.13 support
- FastAPI auto-escaping middleware
- Full HTML entity support
- Unicode handling

## Supported Python Versions

- Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

## Installation

### From source

```bash
git clone https://github.com/pavanepour-k/rysafe.git
cd rysafe
pip install maturin
maturin develop
```

## Quick Start

### Basic Usage

```python
from rysafe import escape, Markup

# Escape HTML characters
dangerous = '<script>alert("XSS")</script>'
safe = escape(dangerous)
print(safe)  # &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;

# Mark string as safe
html = Markup('<strong>Bold text</strong>')
print(html)  # <strong>Bold text</strong>

# Safe string concatenation
result = html + ' & ' + escape('<em>Escaped</em>')
print(result)  # <strong>Bold text</strong> &amp; &lt;em&gt;Escaped&lt;/em&gt;
```

### String Formatting

```python
from rysafe import Markup, escape

# Format strings with auto-escaping
template = Markup('Hello <em>{name}</em>!')
result = template.format(name='<script>alert("XSS")</script>')
print(result)  # Hello <em>&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;</em>!

# Join with auto-escaping
items = ['<tag1>', 'safe', '<tag2>']
result = Markup('<br>').join(items)
print(result)  # &lt;tag1&gt;<br>safe<br>&lt;tag2&gt;
```

### Unescape HTML Entities

```python
from rysafe import Markup

# Unescape HTML entities
escaped = Markup('&lt;div&gt;Hello &amp; welcome&lt;/div&gt;')
unescaped = escaped.unescape()
print(unescaped)  # <div>Hello & welcome</div>

# Common entities
html = Markup('&copy; 2024 &bull; &euro;100 &rarr; &infin;')
print(html.unescape())  # © 2024 • €100 → ∞
```

## FastAPI Integration

rysafe provides seamless FastAPI integration for automatic HTML escaping:

```python
from fastapi import FastAPI
from rysafe import setup_auto_escape, SafeHTMLResponse, Markup

app = FastAPI()

# Enable auto-escaping for all HTML responses
setup_auto_escape(app)

@app.get("/")
def root():
    # This will be auto-escaped
    return {"message": "<script>alert('XSS')</script>"}

@app.get("/html", response_class=SafeHTMLResponse)
def html():
    # This will be auto-escaped
    return "<h1>Hello <script>alert('XSS')</script></h1>"

@app.get("/safe")
def safe():
    # Already marked as safe, won't be escaped
    return Markup("<h1>Hello World</h1>")

# Configure specific paths for auto-escaping
setup_auto_escape(app, paths=["/admin", "/user"])
```

### Middleware Configuration

```python
from fastapi import FastAPI
from rysafe import AutoEscapeMiddleware

app = FastAPI()

# Add middleware with custom configuration
app.add_middleware(
    AutoEscapeMiddleware,
    escape_paths=["/api/html", "/admin"]
)
```

## Migration from MarkupSafe

rysafe is designed as a drop-in replacement for MarkupSafe. Simply replace your imports:

```python
# Before
from markupsafe import Markup, escape

# After  
from rysafe import Markup, escape
```

## Advanced Features

### Custom Objects with `__html__`

```python
from rysafe import Markup, escape

class RichText:
    def __init__(self, text, bold=False):
        self.text = text
        self.bold = bold
    
    def __html__(self):
        if self.bold:
            return f'<strong>{escape(self.text)}</strong>'
        return escape(self.text)

# Automatically uses __html__ method
rich = RichText('Hello <world>', bold=True)
result = Markup('Message: {}').format(rich)
print(result)  # Message: <strong>Hello &lt;world&gt;</strong>
```

### Working with JSON

```python
import json
from rysafe import Markup

# Safe JSON embedding in HTML
data = {"user": "<script>alert('XSS')</script>", "id": 123}
json_str = json.dumps(data)
safe_json = Markup('<script>var data = {};</script>').format(json_str)
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/pavanepour-k/rysafe.git
cd rysafe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
maturin develop
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rysafe --cov-report=html

# Run specific test file
pytest tests/test_escape.py -v
```

### Code Quality

```bash
# Format code
black src/
cargo fmt

# Lint Python
ruff check src/

# Type checking
mypy src/

# Lint Rust
cargo clippy
```

### Building Wheels

```bash
# Build for current platform
maturin build --release

# Build for all platforms (requires Docker)
docker run --rm -v $(pwd):/io ghcr.io/pyo3/maturin build --release
```

## Architecture

rysafe uses a hybrid architecture combining Rust and Python:

```
┌─────────────────┐
│  Python Layer   │  • High-level API
│   (rysafe)      │  • Type annotations  
│                 │  • FastAPI integration
├─────────────────┤
│   PyO3 Bridge   │  • Python ↔ Rust bindings
├─────────────────┤  
│   Rust Core     │  • Performance critical
│ (_rysafe_core)  │  • Memory safety
│                 │  • HTML escaping logic
└─────────────────┘
```

## Acknowledgments

- Inspired by [MarkupSafe](https://github.com/pallets/markupsafe) by Pallets
- Built with [PyO3](https://github.com/PyO3/pyo3) for Python-Rust interop
- Uses [maturin](https://github.com/PyO3/maturin) for building and packaging

## Security

If you discover a security vulnerability, please email security@rysafe.dev instead of using the issue tracker.


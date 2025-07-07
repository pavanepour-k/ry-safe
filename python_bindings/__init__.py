"""rysafe - High-performance HTML/XML escaping library.

A fast, memory-safe HTML/XML escaping library implemented in Rust with
Python bindings. Fully compatible with MarkupSafe API.

Basic usage:
    >>> from rysafe import escape, unescape
    >>> escape('<script>alert("xss")</script>')
    '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
    >>> unescape('&lt;b&gt;bold&lt;/b&gt;')
    '<b>bold</b>'

FastAPI integration:
    >>> from fastapi import FastAPI, Depends
    >>> from rysafe.fastapi_plugin import get_escaper
    >>> app = FastAPI()
    >>> @app.post("/safe")
    ... def safe_endpoint(text: str, escape_fn=Depends(get_escaper)):
    ...     return {"escaped": escape_fn(text)}
"""

__version__ = "0.1.0"
__author__ = "rysafe contributors"
__license__ = "MIT"

try:
    # Import the Rust extension module
    from rysafe.escape import (
        escape,
        escape_silent,
        unescape,
        Markup,
    )
except ImportError as e:
    # Fallback implementation for development or when Rust extension isn't available
    import html
    import warnings
    
    warnings.warn(
        "rysafe Rust extension not available, using Python fallback. "
        "Performance will be significantly reduced. "
        f"Import error: {e}",
        RuntimeWarning,
        stacklevel=2
    )
    
    def escape(s):
        """Fallback HTML escape function using Python's html module."""
        if hasattr(s, '__html__'):
            return s.__html__()
        if isinstance(s, bytes):
            return html.escape(s.decode('utf-8', errors='replace')).encode('utf-8')
        return html.escape(str(s))
    
    def escape_silent(s):
        """Fallback escape_silent function."""
        if s is None:
            return None
        return escape(s)
    
    def unescape(s):
        """Fallback HTML unescape function using Python's html module."""
        if isinstance(s, bytes):
            return html.unescape(s.decode('utf-8', errors='replace')).encode('utf-8')
        return html.unescape(str(s))
    
    class Markup:
        """Fallback Markup class."""
        def __init__(self, content=""):
            self.content = escape(content)
        
        def __str__(self):
            return self.content
        
        def __repr__(self):
            return f"Markup('{self.content}')"
        
        def __add__(self, other):
            if isinstance(other, Markup):
                return Markup(self.content + other.content)
            return Markup(self.content + escape(other))
        
        def __html__(self):
            return self.content

# Re-export for compatibility
from . import fastapi_plugin

# Public API
__all__ = [
    "escape",
    "escape_silent", 
    "unescape",
    "Markup",
    "fastapi_plugin",
    "__version__",
]

# MarkupSafe compatibility aliases
soft_unicode = escape_silent
soft_str = escape_silent

def is_markupsafe_available():
    """Check if MarkupSafe is available for compatibility testing."""
    try:
        import markupsafe
        return True
    except ImportError:
        return False

def get_version_info():
    """Return version information as a tuple."""
    return tuple(map(int, __version__.split('.')))

# Module-level configuration
_default_escape_quotes = True

def set_escape_quotes(value: bool):
    """Configure whether to escape quotes by default.
    
    Args:
        value: Whether to escape quotes (True) or not (False)
    """
    global _default_escape_quotes
    _default_escape_quotes = value

def get_escape_quotes():
    """Get current quote escaping configuration."""
    return _default_escape_quotes
"""
rysafe: High-performance HTML/XML escaping library.

Drop-in replacement for MarkupSafe with Rust performance.
"""

import sys

if sys.version_info < (3, 8):
    raise ImportError("rysafe requires Python 3.8+")

from .markupsafe_compat import ( # noqa: F401, I001
    Markup,
    escape,
    escape_silent,
    soft_str,
    soft_unicode
)

# Try to import FastAPI components, but don't fail if FastAPI is not installed
try:
    from .fastapi_integration import (
        AutoEscapeMiddleware,
        SafeHTMLResponse,
        setup_auto_escape,
    )

    _fastapi_available = True
except ImportError:
    _fastapi_available = False
    SafeHTMLResponse = None
    AutoEscapeMiddleware = None
    setup_auto_escape = None

__version__ = "0.1.0"

# Only include FastAPI components in __all__ if they're available
_base_all = [
    "Markup",
    "escape",
    "escape_silent",
    "soft_str",
    "soft_unicode",
]

if _fastapi_available:
    __all__ = _base_all + [
        "SafeHTMLResponse",
        "AutoEscapeMiddleware",
        "setup_auto_escape",
    ]
else:
    __all__ = _base_all

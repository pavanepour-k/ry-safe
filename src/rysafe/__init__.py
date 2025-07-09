"""
rysafe: High-performance HTML/XML escaping library.

Drop-in replacement for MarkupSafe with Rust performance.
"""

import sys
from typing import TYPE_CHECKING, Any, List, Optional

if sys.version_info < (3, 8):
    raise ImportError("rysafe requires Python 3.8+")

from .markupsafe_compat import (
    Markup,
    escape,
    escape_silent,
    soft_str,
    soft_unicode,
)

# Try to import FastAPI components, but don't fail if FastAPI is not installed
_fastapi_available = False
_SafeHTMLResponse: Any = None
_AutoEscapeMiddleware: Any = None
_setup_auto_escape: Any = None

try:
    from .fastapi_integration import (
        AutoEscapeMiddleware as _AutoEscapeMiddleware,
    )
    from .fastapi_integration import SafeHTMLResponse as _SafeHTMLResponse
    from .fastapi_integration import setup_auto_escape as _setup_auto_escape

    _fastapi_available = True
except ImportError:
    pass

__version__ = "0.1.0"


# Runtime stubs that raise helpful errors when FastAPI is not available
class _FastAPINotInstalledType:
    """Placeholder for FastAPI components when FastAPI is not installed."""

    def __init__(self, name: str):
        self.name = name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise ImportError(
            f"{self.name} requires FastAPI. Install it with:\n"
            "  pip install rysafe[fastapi]\n"
            "Or:\n"
            "  pip install fastapi"
        )

    def __getattr__(self, name: str) -> Any:
        raise ImportError(
            f"{self.name} requires FastAPI. Install it with:\n"
            "  pip install rysafe[fastapi]\n"
            "Or:\n"
            "  pip install fastapi"
        )


# Export FastAPI components based on availability
if TYPE_CHECKING:
    # For type checking, always import the real types
    from .fastapi_integration import (
        AutoEscapeMiddleware,
        SafeHTMLResponse,
        setup_auto_escape,
    )
elif _fastapi_available:
    # Runtime: FastAPI is available
    SafeHTMLResponse = _SafeHTMLResponse
    AutoEscapeMiddleware = _AutoEscapeMiddleware
    setup_auto_escape = _setup_auto_escape
else:
    # Runtime: FastAPI is not available, use stubs
    SafeHTMLResponse = _FastAPINotInstalledType("SafeHTMLResponse")
    AutoEscapeMiddleware = _FastAPINotInstalledType("AutoEscapeMiddleware")
    setup_auto_escape = _FastAPINotInstalledType("setup_auto_escape")

# Define __all__ based on what's available
_base_all = [
    "Markup",
    "escape",
    "escape_silent",
    "soft_str",
    "soft_unicode",
    "__version__",
]

# Always include FastAPI components in __all__ for documentation
__all__ = _base_all + [
    "SafeHTMLResponse",
    "AutoEscapeMiddleware",
    "setup_auto_escape",
]

"""
FastAPI integration for rysafe auto-escaping.

Provides middleware and response handlers for automatic HTML escaping.
"""
import sys
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING or sys.version_info >= (3, 8):
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import HTMLResponse
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.types import ASGIApp, Receive, Scope, Send
        FASTAPI_AVAILABLE = True
    except ImportError:
        FASTAPI_AVAILABLE = False
        # Create dummy classes for when FastAPI is not available
        class FastAPI: pass
        class Request: pass
        class Response: pass
        class HTMLResponse: pass
        class BaseHTTPMiddleware: pass
        ASGIApp = Any
else:
    FASTAPI_AVAILABLE = False

if sys.version_info < (3, 8):
    raise RuntimeError("FastAPI integration requires Python 3.8+")

__all__ = ["SafeHTMLResponse", "AutoEscapeMiddleware", "setup_auto_escape"]


def _check_fastapi_available():
    """Check if FastAPI is available and raise helpful error if not."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is not installed. Install it with: pip install fastapi\n"
            "Or install rysafe with FastAPI support: pip install rysafe[fastapi]"
        )


class SafeHTMLResponse(HTMLResponse):
    """
    HTML response with automatic escaping.
    
    Attributes:
        content: Response content (auto-escaped)
    """
    
    def __init__(self, content: Any = None, **kwargs: Any) -> None:
        """
        Initialize with auto-escaped content.
        
        Args:
            content: Response content
            **kwargs: Additional response parameters
        """
        _check_fastapi_available()
        
        from .markupsafe_compat import Markup, escape
        
        if content is not None and not isinstance(content, Markup):
            content = escape(content)
        super().__init__(content, **kwargs)
    
    def render(self, content: Any) -> bytes:
        """Render content with escaping."""
        from .markupsafe_compat import Markup, escape
        
        if not isinstance(content, Markup):
            content = escape(content)
        return content.encode(self.charset)


class AutoEscapeMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic HTML escaping.
    
    Attributes:
        app: ASGI application
        escape_paths: Paths to auto-escape
    """
    
    def __init__(self, app: ASGIApp, escape_paths: Optional[list] = None) -> None:
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            escape_paths: List of paths to escape
        """
        _check_fastapi_available()
        super().__init__(app)
        self.escape_paths = escape_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with auto-escaping."""
        from .markupsafe_compat import Markup, escape
        
        response = await call_next(request)
        
        if self._should_escape(request.url.path, response):
            if hasattr(response, "body"):
                try:
                    body = response.body.decode("utf-8")
                    if not isinstance(body, Markup):
                        escaped = escape(body)
                        response.body = escaped.encode("utf-8")
                        response.headers["content-length"] = str(len(response.body))
                except (UnicodeDecodeError, AttributeError):
                    pass
        
        return response
    
    def _should_escape(self, path: str, response: Response) -> bool:
        """Check if response should be escaped."""
        if not self.escape_paths:
            content_type = response.headers.get("content-type", "")
            return "text/html" in content_type
        
        return any(path.startswith(p) for p in self.escape_paths)


def setup_auto_escape(app: FastAPI, paths: Optional[list] = None,
                      middleware: bool = True) -> None:
    """
    Configure FastAPI app for auto-escaping.
    
    Args:
        app: FastAPI application
        paths: Paths to auto-escape
        middleware: Enable middleware
    """
    _check_fastapi_available()
    
    if middleware:
        app.add_middleware(AutoEscapeMiddleware, escape_paths=paths)
    
    original_response_class = app.response_class
    
    def safe_response_factory(*args: Any, **kwargs: Any) -> Response:
        """Factory for safe responses."""
        if kwargs.get("media_type") == "text/html":
            return SafeHTMLResponse(*args, **kwargs)
        return original_response_class(*args, **kwargs)
    
    app.response_class = safe_response_factory
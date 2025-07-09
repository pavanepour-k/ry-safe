"""
FastAPI integration for rysafe auto-escaping.

Provides middleware and response handlers for automatic HTML escaping.
"""

import sys
from typing import TYPE_CHECKING, Any, Awaitable, Callable, List, Optional

if sys.version_info < (3, 8):
    raise RuntimeError("FastAPI integration requires Python 3.8+")

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import HTMLResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    if TYPE_CHECKING:
        # Type checking imports
        from fastapi import Request, Response
        from fastapi.responses import HTMLResponse
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.types import ASGIApp

__all__ = ["SafeHTMLResponse", "AutoEscapeMiddleware", "setup_auto_escape"]


def _ensure_fastapi() -> None:
    """Ensure FastAPI is available, raise helpful error if not."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is not installed. Install it with:\n"
            "  pip install fastapi\n"
            "Or install rysafe with FastAPI support:\n"
            "  pip install rysafe[fastapi]"
        )


class SafeHTMLResponse(HTMLResponse):
    """
    HTML response with automatic escaping.

    Automatically escapes any content that isn't already marked as safe
    using the Markup type.

    Example:
        @app.get("/", response_class=SafeHTMLResponse)
        def root():
            return "<h1>Hello World</h1>"  # Will be escaped

        @app.get("/safe", response_class=SafeHTMLResponse)
        def safe():
            return Markup("<h1>Hello World</h1>")  # Won't be escaped
    """

    def __init__(self, content: Any = None, **kwargs: Any) -> None:
        """
        Initialize with auto-escaped content.

        Args:
            content: Response content
            **kwargs: Additional response parameters
        """
        _ensure_fastapi()

        from .markupsafe_compat import Markup, escape

        if content is not None and not isinstance(content, Markup):
            content = escape(content)
        super().__init__(content, **kwargs)

    def render(self, content: Any) -> bytes:
        """Render content with escaping."""
        from .markupsafe_compat import Markup, escape

        if not isinstance(content, Markup):
            content = escape(content)
        return str(content).encode(self.charset)


class AutoEscapeMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic HTML escaping.

    Automatically escapes HTML responses based on content type or
    configured paths.

    Example:
        app = FastAPI()
        app.add_middleware(
            AutoEscapeMiddleware,
            escape_paths=["/admin", "/user"]
        )
    """

    def __init__(
        self, app: ASGIApp, escape_paths: Optional[List[str]] = None
    ) -> None:
        """
        Initialize middleware.

        Args:
            app: ASGI application
            escape_paths: List of paths to escape
        """
        _ensure_fastapi()
        super().__init__(app)
        self.escape_paths = escape_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with auto-escaping."""
        from .markupsafe_compat import Markup, escape

        response = await call_next(request)

        if self._should_escape(request.url.path, response):
            if hasattr(response, "body"):
                try:
                    # Handle both bytes and memoryview
                    body_data = response.body
                    if isinstance(body_data, memoryview):
                        body_data = body_data.tobytes()

                    body = body_data.decode("utf-8")
                    if not isinstance(body, Markup):
                        escaped = escape(body)
                        response.body = str(escaped).encode("utf-8")
                        # Update content length
                        response.headers["content-length"] = str(
                            len(response.body)
                        )
                except (UnicodeDecodeError, AttributeError):
                    # Skip binary responses or decode errors
                    pass

        return response

    def _should_escape(self, path: str, response: Response) -> bool:
        """Determine if response should be auto-escaped."""
        # Check content type
        content_type = response.headers.get("content-type", "")
        is_html = "text/html" in content_type

        # If specific paths are configured, use those
        if self.escape_paths:
            path_match = any(path.startswith(p) for p in self.escape_paths)
            return is_html and path_match

        # Otherwise, escape all HTML responses
        return is_html


def setup_auto_escape(
    app: Any,
    paths: Optional[List[str]] = None,
    middleware: bool = True,
    default_response_class: bool = True,
) -> None:
    """
    Configure FastAPI app for auto-escaping.

    Args:
        app: FastAPI application instance
        paths: Optional list of paths to auto-escape (None = all HTML)
        middleware: Enable auto-escape middleware
        default_response_class: Set SafeHTMLResponse as default for HTML

    Example:
        app = FastAPI()
        setup_auto_escape(app)

        # Or with specific paths
        setup_auto_escape(app, paths=["/admin", "/api/html"])
    """
    _ensure_fastapi()

    # Import here to ensure FastAPI is available
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError(f"Expected FastAPI instance, got {type(app).__name__}")

    if middleware:
        app.add_middleware(AutoEscapeMiddleware, escape_paths=paths)

    if default_response_class:
        # Store original response class
        original_response_class = getattr(app, "response_class", Response)

        def safe_response_factory(*args: Any, **kwargs: Any) -> Any:
            """Factory for safe responses."""
            # Check if this should be an HTML response
            media_type = kwargs.get("media_type", "")

            # If explicitly set to HTML, use SafeHTMLResponse
            if media_type == "text/html":
                kwargs.pop("response_class", None)  # Remove if present
                return SafeHTMLResponse(*args, **kwargs)

            # Otherwise use original response class
            return original_response_class(*args, **kwargs)

        # Set the factory as the default response class
        # FastAPI dynamically adds response_class attribute, so we use setattr
        setattr(app, "response_class", safe_response_factory)

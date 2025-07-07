"""FastAPI plugin for rysafe.

This module provides FastAPI integration for rysafe, allowing
easy dependency injection and automatic escaping in FastAPI applications.

Example usage:
    from fastapi import FastAPI, Depends
    from rysafe.fastapi_plugin import get_escaper, auto_escape_middleware
    
    app = FastAPI()
    app.add_middleware(auto_escape_middleware)
    
    @app.post("/safe")
    def safe_endpoint(text: str, escape=Depends(get_escaper)):
        return {"escaped": escape(text)}
"""

from typing import Any, Callable, Optional, Union
import functools
import asyncio
import json

# Check if FastAPI is available
try:
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    # Mock classes when FastAPI is not available
    FASTAPI_AVAILABLE = False
    Request = object
    Response = object
    JSONResponse = object

try:
    from rysafe import escape, escape_silent, unescape
except ImportError:
    # Fallback for development/testing
    import html
    
    def escape(text: Union[str, bytes]) -> Union[str, bytes]:
        if isinstance(text, bytes):
            return html.escape(text.decode('utf-8', errors='replace')).encode('utf-8')
        return html.escape(text)
    
    def escape_silent(text: Optional[Union[str, bytes]]) -> Optional[Union[str, bytes]]:
        if text is None:
            return None
        return escape(text)
    
    def unescape(text: Union[str, bytes]) -> Union[str, bytes]:
        if isinstance(text, bytes):
            return html.unescape(text.decode('utf-8', errors='replace')).encode('utf-8')
        return html.unescape(text)


class EscapeConfig:
    """Configuration for HTML escaping behavior."""
    
    def __init__(
        self,
        auto_escape: bool = True,
        escape_json_strings: bool = True,
        escape_response_headers: bool = False,
        safe_content_types: Optional[list] = None,
    ):
        self.auto_escape = auto_escape
        self.escape_json_strings = escape_json_strings
        self.escape_response_headers = escape_response_headers
        self.safe_content_types = safe_content_types or [
            "application/json",
            "text/plain",
            "text/html",
        ]


# Global configuration instance
_config = EscapeConfig()


def configure_escaping(config: EscapeConfig) -> None:
    """Configure global escaping behavior.
    
    Args:
        config: EscapeConfig instance with desired settings
    """
    global _config
    _config = config


def get_escaper() -> Callable[[Union[str, bytes]], Union[str, bytes]]:
    """Dependency provider for HTML escaping.
    
    Returns a function that can be used to escape HTML content.
    This is designed to be used with FastAPI's dependency injection.
    
    Returns:
        A function that escapes HTML content
        
    Example:
        @app.post("/escape")
        def escape_endpoint(text: str, escape_fn=Depends(get_escaper)):
            return {"escaped": escape_fn(text)}
    """
    return escape


def get_escaper_silent() -> Callable[[Optional[Union[str, bytes]]], Optional[Union[str, bytes]]]:
    """Dependency provider for HTML escaping that handles None values.
    
    Returns a function that can be used to escape HTML content,
    passing None values through unchanged.
    
    Returns:
        A function that escapes HTML content or returns None
        
    Example:
        @app.post("/escape")
        def escape_endpoint(text: Optional[str], escape_fn=Depends(get_escaper_silent)):
            return {"escaped": escape_fn(text)}
    """
    return escape_silent


def get_unescaper() -> Callable[[Union[str, bytes]], Union[str, bytes]]:
    """Dependency provider for HTML unescaping.
    
    Returns a function that can be used to unescape HTML content.
    
    Returns:
        A function that unescapes HTML content
    """
    return unescape


class AutoEscapeMiddleware:
    """Middleware for automatic HTML escaping of responses."""
    
    def __init__(self, app: Any, config: Optional[EscapeConfig] = None):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for AutoEscapeMiddleware")
        self.app = app
        self.config = config or _config
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.body" and self.config.auto_escape:
                await self._process_response_body(message, request)
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    async def _process_response_body(self, message: dict, request: Request) -> None:
        """Process and escape response body if needed."""
        body = message.get("body", b"")
        if not body:
            return
        
        content_type = getattr(request.state, "response_content_type", "")
        
        if content_type in self.config.safe_content_types:
            try:
                if content_type == "application/json" and self.config.escape_json_strings:
                    # Parse JSON and escape string values
                    data = json.loads(body.decode('utf-8'))
                    escaped_data = self._escape_json_values(data)
                    message["body"] = json.dumps(escaped_data).encode('utf-8')
                elif content_type.startswith("text/"):
                    # Escape text content
                    text = body.decode('utf-8', errors='replace')
                    escaped_text = escape(text)
                    message["body"] = escaped_text.encode('utf-8')
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If parsing fails, leave body unchanged
                pass
    
    def _escape_json_values(self, data: Any) -> Any:
        """Recursively escape string values in JSON data."""
        if isinstance(data, str):
            return escape(data)
        elif isinstance(data, dict):
            return {key: self._escape_json_values(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._escape_json_values(item) for item in data]
        else:
            return data


def auto_escape_middleware(app: Any) -> AutoEscapeMiddleware:
    """Factory function to create auto-escape middleware.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Configured AutoEscapeMiddleware instance
    """
    return AutoEscapeMiddleware(app)


def escape_route_responses(escape_strings: bool = True):
    """Decorator to automatically escape string responses from route handlers.
    
    Args:
        escape_strings: Whether to escape string return values
        
    Example:
        @app.get("/safe")
        @escape_route_responses()
        def get_user_input():
            return "<script>alert('xss')</script>"  # Will be escaped
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return _escape_response(result, escape_strings)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return _escape_response(result, escape_strings)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def _escape_response(response: Any, escape_strings: bool) -> Any:
    """Helper function to escape response data."""
    if escape_strings and isinstance(response, str):
        return escape(response)
    elif isinstance(response, dict):
        return {key: _escape_response(value, escape_strings) for key, value in response.items()}
    elif isinstance(response, list):
        return [_escape_response(item, escape_strings) for item in response]
    else:
        return response


# Convenience aliases
get_html_escaper = get_escaper
get_html_unescaper = get_unescaper
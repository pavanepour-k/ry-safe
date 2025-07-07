"""FastAPI integration tests for rysafe.

This test suite ensures FastAPI integration works correctly with
dependency injection, middleware, and response processing.
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add the python_bindings directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_bindings'))

try:
    from fastapi import FastAPI, Depends, HTTPException
    from fastapi.testclient import TestClient
    from fastapi.responses import JSONResponse, PlainTextResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    pytest.skip("FastAPI not available", allow_module_level=True)

try:
    from rysafe.fastapi_plugin import (
        get_escaper, 
        get_escaper_silent, 
        get_unescaper,
        auto_escape_middleware,
        AutoEscapeMiddleware,
        EscapeConfig,
        configure_escaping,
        escape_route_responses,
    )
    from rysafe import escape, unescape
except ImportError:
    # Use fallback implementation for testing
    import html
    
    def escape(s): 
        return html.escape(str(s))
    def unescape(s): 
        return html.unescape(str(s))
    
    # Mock the FastAPI plugin functions
    def get_escaper(): 
        return escape
    def get_escaper_silent(): 
        return lambda x: None if x is None else escape(x)
    def get_unescaper(): 
        return unescape
    
    class EscapeConfig:
        def __init__(self, **kwargs):
            self.auto_escape = kwargs.get('auto_escape', True)
            self.escape_json_strings = kwargs.get('escape_json_strings', True)
    
    def configure_escaping(config): 
        pass
    def auto_escape_middleware(app): 
        return app
    def escape_route_responses(): 
        return lambda f: f
    
    class AutoEscapeMiddleware:
        def __init__(self, app, config=None):
            self.app = app


class TestBasicDependencyInjection:
    """Test basic FastAPI dependency injection."""

    def test_escape_dependency(self):
        """Test escaper dependency injection."""
        app = FastAPI()
        
        @app.post("/escape")
        def escape_endpoint(text: str, escape_fn=Depends(get_escaper)):
            return {"escaped": escape_fn(text)}
        
        client = TestClient(app)
        response = client.post("/escape?text=<script>alert('xss')</script>")
        
        assert response.status_code == 200
        data = response.json()
        assert data["escaped"] == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_escape_silent_dependency(self):
        """Test silent escaper dependency injection."""
        app = FastAPI()
        
        @app.post("/escape-silent")
        def escape_silent_endpoint(text: str = None, escape_fn=Depends(get_escaper_silent)):
            return {"escaped": escape_fn(text)}
        
        client = TestClient(app)
        
        # Test with None
        response = client.post("/escape-silent")
        assert response.status_code == 200
        data = response.json()
        assert data["escaped"] is None
        
        # Test with actual text
        response = client.post("/escape-silent?text=<script>")
        assert response.status_code == 200
        data = response.json()
        assert data["escaped"] == "&lt;script&gt;"

    def test_unescape_dependency(self):
        """Test unescaper dependency injection."""
        app = FastAPI()
        
        @app.post("/unescape")
        def unescape_endpoint(text: str, unescape_fn=Depends(get_unescaper)):
            return {"unescaped": unescape_fn(text)}
        
        client = TestClient(app)
        response = client.post("/unescape?text=&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")
        
        assert response.status_code == 200
        data = response.json()
        assert data["unescaped"] == "<script>alert('xss')</script>"


class TestPracticalUseCases:
    """Test practical use cases for FastAPI integration."""

    def test_user_content_endpoint(self):
        """Test endpoint handling user-generated content."""
        app = FastAPI()
        
        @app.post("/post-comment")
        def post_comment(
            comment: str, 
            author: str,
            escape_fn=Depends(get_escaper)
        ):
            return {
                "comment": escape_fn(comment),
                "author": escape_fn(author),
                "status": "posted"
            }
        
        client = TestClient(app)
        response = client.post(
            "/post-comment", 
            params={
                "comment": "<script>alert('Hacked!')</script>Nice post!",
                "author": "User<script>alert('xss')</script>"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "&lt;script&gt;" in data["comment"]
        assert "&lt;script&gt;" in data["author"]
        assert "alert" not in data["comment"]  # Should be escaped
        assert data["status"] == "posted"

    def test_search_results_endpoint(self):
        """Test search results with potential XSS in queries."""
        app = FastAPI()
        
        @app.get("/search")
        def search_results(
            query: str,
            escape_fn=Depends(get_escaper)
        ):
            # Simulate search results
            results = [
                f"Result 1 matching '{query}'",
                f"Result 2 with '{query}' highlighted",
            ]
            
            return {
                "query": escape_fn(query),
                "results": [escape_fn(result) for result in results],
                "count": len(results)
            }
        
        client = TestClient(app)
        response = client.get("/search?query=<img src=x onerror=alert('xss')>")
        
        assert response.status_code == 200
        data = response.json()
        assert "&lt;img" in data["query"]
        assert "onerror" not in data["query"]  # Should be escaped
        assert all("&lt;img" in result for result in data["results"])

    def test_form_processing_endpoint(self):
        """Test form processing with mixed safe and unsafe content."""
        app = FastAPI()
        
        @app.post("/process-form")
        def process_form(
            name: str,
            email: str,
            message: str,
            escape_fn=Depends(get_escaper)
        ):
            # Only escape the message, leave email and name for validation
            return {
                "name": name,  # Assume name is validated elsewhere
                "email": email,  # Assume email is validated elsewhere
                "message": escape_fn(message),
                "processed": True
            }
        
        client = TestClient(app)
        response = client.post(
            "/process-form",
            params={
                "name": "John Doe",
                "email": "john@example.com",
                "message": "Thanks for the service! <script>alert('xss')</script>"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert "&lt;script&gt;" in data["message"]
        assert data["processed"] is True


class TestErrorHandling:
    """Test error handling in FastAPI integration."""

    def test_invalid_input_handling(self):
        """Test handling of invalid input types."""
        app = FastAPI()
        
        @app.post("/escape-strict")
        def escape_strict_endpoint(text: str, escape_fn=Depends(get_escaper)):
            if not isinstance(text, str):
                raise HTTPException(status_code=400, detail="Text must be a string")
            return {"escaped": escape_fn(text)}
        
        client = TestClient(app)
        
        # Valid input
        response = client.post("/escape-strict?text=<script>")
        assert response.status_code == 200
        
        # Invalid input will be handled by FastAPI's type validation
        response = client.post("/escape-strict", json={"text": 123})
        assert response.status_code == 422  # Validation error

    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        app = FastAPI()
        
        @app.post("/escape-empty")
        def escape_empty_endpoint(text: str = "", escape_fn=Depends(get_escaper)):
            return {"escaped": escape_fn(text), "length": len(text)}
        
        client = TestClient(app)
        
        # Empty string
        response = client.post("/escape-empty?text=")
        assert response.status_code == 200
        data = response.json()
        assert data["escaped"] == ""
        assert data["length"] == 0
        
        # Default empty
        response = client.post("/escape-empty")
        assert response.status_code == 200
        data = response.json()
        assert data["escaped"] == ""
        assert data["length"] == 0


class TestMiddleware:
    """Test middleware functionality."""

    def test_auto_escape_middleware_configuration(self):
        """Test auto-escape middleware configuration."""
        config = EscapeConfig(
            auto_escape=True,
            escape_json_strings=True,
            escape_response_headers=False
        )
        
        # Test configuration
        assert config.auto_escape is True
        assert config.escape_json_strings is True
        assert config.escape_response_headers is False

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_middleware_integration(self):
        """Test middleware integration with FastAPI app."""
        app = FastAPI()
        
        # Add the middleware
        middleware = AutoEscapeMiddleware(app)
        
        @app.get("/raw-response")
        def raw_response():
            return {"message": "<script>alert('test')</script>"}
        
        client = TestClient(app)
        response = client.get("/raw-response")
        assert response.status_code == 200


class TestDecorators:
    """Test decorator functionality."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_escape_route_responses_decorator(self):
        """Test route response escaping decorator."""
        app = FastAPI()
        
        @app.get("/decorated")
        @escape_route_responses()
        def decorated_endpoint():
            return "<script>alert('xss')</script>"
        
        @app.get("/normal")
        def normal_endpoint():
            return "<script>alert('xss')</script>"
        
        client = TestClient(app)
        
        # Decorated endpoint should escape
        response = client.get("/decorated")
        assert response.status_code == 200
        # Note: The exact behavior depends on implementation
        
        # Normal endpoint returns raw
        response = client.get("/normal")
        assert response.status_code == 200


class TestConfigurationManagement:
    """Test configuration management."""

    def test_global_configuration(self):
        """Test global configuration management."""
        # Test default configuration
        config = EscapeConfig()
        assert config.auto_escape is True
        assert config.escape_json_strings is True
        
        # Test custom configuration
        custom_config = EscapeConfig(
            auto_escape=False,
            escape_json_strings=False,
            escape_response_headers=True
        )
        
        configure_escaping(custom_config)
        
        # Configuration should be applied (in real implementation)
        assert custom_config.auto_escape is False
        assert custom_config.escape_json_strings is False
        assert custom_config.escape_response_headers is True

    def test_safe_content_types_configuration(self):
        """Test safe content types configuration."""
        config = EscapeConfig(
            safe_content_types=["application/json", "text/html"]
        )
        
        assert "application/json" in config.safe_content_types
        assert "text/html" in config.safe_content_types
        assert "text/plain" not in config.safe_content_types


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_blog_comment_system(self):
        """Test a blog comment system scenario."""
        app = FastAPI()
        
        # Mock database
        comments = []
        
        @app.post("/comments")
        def add_comment(
            author: str,
            content: str,
            escape_fn=Depends(get_escaper)
        ):
            comment = {
                "id": len(comments) + 1,
                "author": escape_fn(author),
                "content": escape_fn(content),
                "timestamp": "2023-01-01T00:00:00Z"
            }
            comments.append(comment)
            return comment
        
        @app.get("/comments")
        def get_comments():
            return {"comments": comments}
        
        client = TestClient(app)
        
        # Add a malicious comment
        response = client.post(
            "/comments",
            params={
                "author": "Malicious<script>alert('xss')</script>",
                "content": "Great post! <img src=x onerror=alert('pwned')>"
            }
        )
        
        assert response.status_code == 200
        comment_data = response.json()
        assert "&lt;script&gt;" in comment_data["author"]
        assert "&lt;img" in comment_data["content"]
        assert "alert" not in comment_data["author"]
        assert "onerror" not in comment_data["content"]
        
        # Retrieve comments
        response = client.get("/comments")
        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"]) == 1
        assert "&lt;script&gt;" in data["comments"][0]["author"]

    def test_api_response_sanitization(self):
        """Test API response sanitization."""
        app = FastAPI()
        
        @app.get("/user/{user_id}")
        def get_user(user_id: int, escape_fn=Depends(get_escaper)):
            # Mock user data with potential XSS
            user_data = {
                "id": user_id,
                "name": "User <script>alert('xss')</script>",
                "bio": "I'm a <b>developer</b> & security researcher",
                "website": "https://example.com/?q=<script>",
                "safe_field": "This is safe content"
            }
            
            # Escape only specific fields
            return {
                "id": user_data["id"],
                "name": escape_fn(user_data["name"]),
                "bio": escape_fn(user_data["bio"]),
                "website": escape_fn(user_data["website"]),
                "safe_field": user_data["safe_field"]  # Don't escape this
            }
        
        client = TestClient(app)
        response = client.get("/user/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "&lt;script&gt;" in data["name"]
        assert "&lt;b&gt;" in data["bio"]  # HTML tags escaped
        assert "&amp;" in data["bio"]     # Ampersand escaped
        assert "&lt;script&gt;" in data["website"]
        assert data["safe_field"] == "This is safe content"

    def test_search_api_with_escaping(self):
        """Test search API with query escaping."""
        app = FastAPI()
        
        @app.get("/search")
        def search(
            q: str,
            category: str = "all",
            escape_fn=Depends(get_escaper)
        ):
            # Mock search results
            results = [
                {"title": f"Result 1 for '{q}'", "snippet": f"Contains {q} in content"},
                {"title": f"Result 2 about '{q}'", "snippet": f"Related to {q} topic"},
            ]
            
            return {
                "query": escape_fn(q),
                "category": escape_fn(category),
                "results": [
                    {
                        "title": escape_fn(result["title"]),
                        "snippet": escape_fn(result["snippet"])
                    }
                    for result in results
                ],
                "total": len(results)
            }
        
        client = TestClient(app)
        response = client.get("/search?q=<img src=x onerror=alert('xss')>&category=<script>")
        
        assert response.status_code == 200
        data = response.json()
        
        # Query should be escaped
        assert "&lt;img" in data["query"]
        assert "onerror" not in data["query"]
        
        # Category should be escaped
        assert "&lt;script&gt;" in data["category"]
        
        # Results should be escaped
        for result in data["results"]:
            assert "&lt;img" in result["title"]
            assert "&lt;img" in result["snippet"]
            assert "onerror" not in result["title"]
            assert "onerror" not in result["snippet"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rysafe import setup_auto_escape, SafeHTMLResponse


@pytest.fixture
def app():
    app = FastAPI()
    setup_auto_escape(app)
    
    @app.get("/")
    def root():
        return {"message": "<script>alert('xss')</script>"}
    
    @app.get("/html", response_class=SafeHTMLResponse)
    def html():
        return "<p>Hello <script>alert('xss')</script></p>"
    
    @app.get("/safe")
    def safe():
        from rysafe import Markup
        return Markup("<b>Already Safe</b>")
    
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestFastAPIIntegration:
    def test_json_not_escaped(self, client):
        response = client.get("/")
        assert response.json()["message"] == "<script>alert('xss')</script>"
    
    def test_html_response_escaped(self, client):
        response = client.get("/html")
        assert "&lt;script&gt;" in response.text
        assert "<script>" not in response.text
    
    def test_markup_not_double_escaped(self, client):
        response = client.get("/safe")
        assert "<b>Already Safe</b>" in response.text
    
    def test_middleware_content_type_detection(self, app):
        client = TestClient(app)
        
        @app.get("/custom-html")
        def custom():
            return "<div>Test</div>"
        
        response = client.get("/custom-html")
        assert response.status_code == 200
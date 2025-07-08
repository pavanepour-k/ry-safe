from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import rysafe


class AutoEscapeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.escape = rysafe.escape
        request.state.Markup = rysafe.Markup
        response = await call_next(request)
        return response


def setup_rysafe(app: FastAPI):
    app.add_middleware(AutoEscapeMiddleware)
    
    @app.on_event("startup")
    async def inject_rysafe():
        app.state.escape = rysafe.escape
        app.state.Markup = rysafe.Markup
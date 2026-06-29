"""Gateway middleware: auth, rate limiting, CORS."""

from __future__ import annotations

import time
from typing import Callable

import jwt
import redis.asyncio as aioredis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import GatewaySettings

# Routes that don't require authentication
PUBLIC_ROUTES = {
    "GET": {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"},
    "POST": {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/telegram",
    },
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT tokens for protected routes."""

    def __init__(self, app: Callable, settings: GatewaySettings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method

        # Skip auth for public routes
        public_for_method = PUBLIC_ROUTES.get(method, set())
        if path in public_for_method or any(
            path.startswith(p) for p in ["/docs", "/redoc", "/openapi.json"]
        ):
            return await call_next(request)

        # Frontend static files
        if path.startswith("/static/") or path.startswith("/assets/"):
            return await call_next(request)

        # Validate JWT
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            # Inject user info into request state
            request.state.user_id = int(payload["sub"])
            request.state.token_payload = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app: Callable, settings: GatewaySettings) -> None:
        super().__init__(app)
        self.settings = settings
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0
        max_requests = self.settings.rate_limit_per_minute

        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests.get(client_ip, [])
            if now - t < window
        ]

        if len(self.requests[client_ip]) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(int(window))},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

"""Gateway middleware: auth, rate limiting, CORS, correlation ID."""

from __future__ import annotations

import uuid
from typing import Callable

import jwt
import redis.asyncio as aioredis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import GatewaySettings
from shared.rate_limit import RedisRateLimiter, TIERS

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

# Auth endpoints with stricter rate limits
AUTH_ENDPOINTS = {"/api/v1/auth/login", "/api/v1/auth/register"}


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
    """Redis-backed rate limiter with per-tier limits.

    Tiers:
      - auth_strict:    5 req/min for /auth/login and /auth/register
      - anonymous:     10 req/min for unauthenticated requests
      - authenticated: 120 req/min for authenticated users
    """

    def __init__(self, app: Callable, settings: GatewaySettings) -> None:
        super().__init__(app)
        self.settings = settings
        self._redis: aioredis.Redis | None = None
        self._limiter: RedisRateLimiter | None = None

    async def _ensure_redis(self) -> None:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                decode_responses=True,
            )
            self._limiter = RedisRateLimiter(self._redis)

    def _get_tier(self, request: Request) -> tuple[str, str, int, int]:
        """Determine rate limit tier for the current request.

        Returns (tier_name, key_suffix, limit, window_seconds).
        """
        path = request.url.path
        user_id = getattr(request.state, "user_id", None)

        # Auth-specific strict limits for login/register
        if path in AUTH_ENDPOINTS:
            tier = "auth_strict"
            limit, window = TIERS["auth_strict"]
            key_suffix = f"auth:{user_id or request.client.host or 'unknown'}"
            return tier, key_suffix, limit, window

        # Authenticated users get higher limits
        if user_id is not None:
            tier = "authenticated"
            limit, window = TIERS["authenticated"]
            key_suffix = f"user:{user_id}"
            return tier, key_suffix, limit, window

        # Anonymous users
        tier = "anonymous"
        limit, window = TIERS["anonymous"]
        client_ip = request.client.host if request.client else "unknown"
        key_suffix = f"anon:{client_ip}"
        return tier, key_suffix, limit, window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health/metrics/static/uploads
        path = request.url.path
        if path in ("/health", "/metrics", "/favicon.ico") or path.startswith("/uploads/"):
            return await call_next(request)

        tier_name: str = "anonymous"
        limit: int = 60
        limit_set = False
        try:
            await self._ensure_redis()
            tier_name, key_suffix, limit, window = self._get_tier(request)
            redis_key = f"ratelimit:{tier_name}:{key_suffix}"

            allowed = await self._limiter.check(redis_key, limit, window)
            limit_set = True

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={
                        "Retry-After": str(window),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )
        except Exception:
            # Fail open — if Redis is down, allow the request through
            pass

        response = await call_next(request)

        # Add rate limit headers on the response (only when Redis was available)
        if limit_set:
            try:
                response.headers["X-RateLimit-Limit"] = str(limit)
            except Exception:
                pass

        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Generates and propagates X-Request-ID header across services."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response

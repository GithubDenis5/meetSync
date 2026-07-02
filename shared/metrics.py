"""Prometheus metrics utilities with middleware for auto-instrumentation."""

from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# HTTP metrics
http_request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Business metrics
active_users = Gauge("active_users_total", "Total active users")
active_groups = Gauge("active_groups_total", "Total active groups")
votes_active = Gauge("votes_active_total", "Currently active votes")
notifications_sent = Counter("notifications_sent_total", "Total notifications sent")
events_published = Counter("events_published_total", "Total events published", ["event_type"])

# Infrastructure metrics
db_pool_size = Gauge("db_pool_size", "Database connection pool size")
rabbitmq_connected = Gauge("rabbitmq_connection_status", "RabbitMQ connection status (1=connected, 0=disconnected)")
websocket_connections_active = Gauge("websocket_connections_active", "Active WebSocket connections per user")


class PrometheusMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that records HTTP request count and duration for every request."""

    def __init__(self, app: Any, service_name: str) -> None:
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        method = request.method
        path = request.url.path
        start_time = time.monotonic()
        try:
            response = await call_next(request)
            return response
        finally:
            duration = time.monotonic() - start_time
            http_request_count.labels(self.service_name, method, path, getattr(response, "status_code", 500)).inc()
            http_request_duration.labels(self.service_name, method, path).observe(duration)


def add_prometheus_middleware(app: Any, service_name: str) -> None:
    """Register Prometheus middleware and /metrics endpoint on a FastAPI app.

    Call this immediately after creating the FastAPI instance:
        app = FastAPI(...)
        add_prometheus_middleware(app, "auth-service")
    """
    from fastapi import FastAPI

    app.add_middleware(PrometheusMiddleware, service_name=service_name)  # type: ignore[arg-type]

    # Only add /metrics if not already registered (e.g. gateway already has one)
    has_metrics = any(getattr(r, "path", None) == "/metrics" for r in app.routes)
    if not has_metrics:

        @app.get("/metrics")  # type: ignore[arg-type]
        async def metrics() -> Response:
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def get_metrics() -> bytes:
    """Return latest metrics."""
    return generate_latest()

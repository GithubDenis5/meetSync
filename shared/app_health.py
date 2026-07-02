"""Health and lifecycle helpers for FastAPI services.

Provides standardized /live and /ready endpoints.
Every service already has its own /health endpoint.

Usage:
    from shared.app_health import add_lifecycle

    app = FastAPI(...)
    add_lifecycle(app, "my-service")

For readiness probes with dependency checking, pass them explicitly:
    add_lifecycle(app, "my-service", db_manager=db, rmq=rmq)
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI


def add_lifecycle(
    app: FastAPI,
    service_name: str,
    db_manager: Any = None,
    rmq: Any = None,
    redis_client: Any = None,
) -> None:
    """Add /live and /ready endpoints to a FastAPI app.

    These are lightweight probes for container health checks.
    Pass dependencies (db_manager, rmq, redis_client) to enable
    dependency-specific readiness probes.
    """
    existing = {getattr(r, "path", None) for r in app.routes}

    if "/live" not in existing:
        @app.get("/live")
        async def live() -> dict:
            return {"service": service_name, "status": "alive"}

    if "/ready" not in existing:
        @app.get("/ready")
        async def ready() -> dict:
            statuses = {"service": service_name, "status": "ready"}
            if db_manager:
                try:
                    from sqlalchemy import text
                    async with db_manager.engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                    statuses["db"] = "ok"
                except Exception as e:
                    statuses["db"] = f"error: {e}"
                    statuses["status"] = "degraded"
            if rmq:
                try:
                    is_connected = getattr(rmq, '_connection', None) is not None
                    statuses["rabbitmq"] = "connected" if is_connected else "disconnected"
                    if not is_connected:
                        statuses["status"] = "degraded"
                except Exception as e:
                    statuses["rabbitmq"] = f"error: {e}"
                    statuses["status"] = "degraded"
            if redis_client:
                try:
                    await redis_client.ping()
                    statuses["redis"] = "ok"
                except Exception as e:
                    statuses["redis"] = f"error: {e}"
                    statuses["status"] = "degraded"
            return statuses

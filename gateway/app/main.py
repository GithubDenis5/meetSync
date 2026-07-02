"""API Gateway — single entry point for MeetSync."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared.logging import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import GatewaySettings
from app.middleware import AuthMiddleware, CorrelationIdMiddleware, RateLimitMiddleware
from app.router import router
from app.upload import router as upload_router
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("gateway", "DEBUG" if "DEBUG" in __import__("os").environ.get("DEBUG", "") else "INFO")
logger = logging.getLogger("gateway")

settings = GatewaySettings()

app = FastAPI(
    title="MeetSync API Gateway",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID (outermost — generates ID before any processing)
app.add_middleware(CorrelationIdMiddleware)  # type: ignore[arg-type]

# Rate limiting
app.add_middleware(RateLimitMiddleware, settings=settings)  # type: ignore[arg-type]

# Auth middleware
app.add_middleware(AuthMiddleware, settings=settings)  # type: ignore[arg-type]

# Prometheus metrics
add_prometheus_middleware(app, "gateway")

# Lifecycle endpoints
add_lifecycle(app, "gateway")

# Upload router (before proxy — handles multipart locally)
app.include_router(upload_router)

# Serve uploaded files
uploads_dir = Path(settings.upload_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Proxy router (catch-all for microservice API routes)
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"service": "gateway", "status": "ok"}


@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

"""API Gateway — single entry point for MeetSync."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import GatewaySettings
from app.middleware import AuthMiddleware, RateLimitMiddleware
from app.router import router

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

# Rate limiting
app.add_middleware(RateLimitMiddleware, settings=settings)  # type: ignore[arg-type]

# Auth middleware
app.add_middleware(AuthMiddleware, settings=settings)  # type: ignore[arg-type]

# Routers
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"service": "gateway", "status": "ok"}


@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

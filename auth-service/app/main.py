"""Auth Service — registration, login, JWT, OAuth."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import AuthSettings
from app.routes import router

logger = logging.getLogger("auth-service")
settings = AuthSettings()

app = FastAPI(
    title="MeetSync - Auth Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"service": "auth-service", "status": "ok"}

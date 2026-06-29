"""Auth Service — registration, login, JWT, OAuth."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import AuthSettings
from app.routes import router
from shared.database import DatabaseManager
import shared.models  # noqa: F401 — register all models on Base.metadata

logger = logging.getLogger("auth-service")
settings = AuthSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup if they don't exist."""
    logger.info("Running database migrations (create_all)...")
    try:
        await db_manager.create_all()
        logger.info("Database tables ready")
    except Exception as e:
        logger.warning("Could not create tables (may already exist): %s", e)
    yield
    await db_manager.close()


app = FastAPI(
    title="MeetSync - Auth Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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

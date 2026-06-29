"""FastAPI app factory for all services."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST

from shared.config import Settings, get_settings
from shared.database import DatabaseManager
from shared.exceptions import AppException
from shared.logging import setup_logging
from shared.metrics import get_metrics
from shared.rabbitmq.client import RabbitMQClient

logger = logging.getLogger("shared.app")


class ServiceApp:
    """Factory for creating FastAPI applications for each microservice."""

    def __init__(
        self,
        service_name: str,
        settings: Optional[Settings] = None,
        enable_db: bool = True,
        enable_rabbitmq: bool = False,
        enable_redis: bool = False,
    ) -> None:
        self.service_name = service_name
        self.settings = settings or get_settings()
        self.settings.service_name = service_name
        self.settings.service_port = int(getattr(self.settings, f"{service_name.replace('-', '_')}_port", 8000))

        setup_logging(service_name, "DEBUG" if self.settings.debug else "INFO")

        self.db: Optional[DatabaseManager] = None
        self.rmq: Optional[RabbitMQClient] = None
        self.enable_db = enable_db
        self.enable_rabbitmq = enable_rabbitmq

        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            await self._startup()
            yield
            await self._shutdown()

        app = FastAPI(
            title=f"{self.settings.project_name} - {self.service_name}",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            lifespan=lifespan,
        )

        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Exception handler
        @app.exception_handler(AppException)
        async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        # Metrics endpoint
        @app.get("/metrics")
        async def metrics() -> Response:
            return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)

        # Health check
        @app.get("/health")
        async def health() -> dict:
            return {
                "service": self.service_name,
                "status": "ok",
                "db_connected": self.db is not None,
                "rmq_connected": self.rmq is not None,
            }

        return app

    async def _startup(self) -> None:
        """Initialize connections on startup."""
        logger.info("Starting %s service", self.service_name)

        if self.enable_db:
            self.db = DatabaseManager(self.settings)
            logger.info("Database connection initialized")

        if self.enable_rabbitmq:
            self.rmq = RabbitMQClient(self.settings)
            await self.rmq.connect()
            logger.info("RabbitMQ connection initialized")

    async def _shutdown(self) -> None:
        """Clean up connections on shutdown."""
        logger.info("Shutting down %s service", self.service_name)

        if self.rmq:
            await self.rmq.disconnect()

        if self.db:
            await self.db.close()

    def get_app(self) -> FastAPI:
        return self.app

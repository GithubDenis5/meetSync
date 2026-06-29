"""Configuration management for all services."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Base settings for all MeetSync services."""

    # Project
    project_name: str = "MeetSync"
    environment: str = "development"
    debug: bool = True
    service_name: str = "unknown"
    service_port: int = 8000

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "meetsync"
    postgres_user: str = "meetsync"
    postgres_password: str = "meetsync_secret_pass"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "meetsync"
    rabbitmq_password: str = "meetsync_rabbit_pass"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

    # JWT
    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Rate limiting
    rate_limit_per_minute: int = 60

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # Service URLs
    auth_service_url: str = "http://auth-service:8001"
    user_service_url: str = "http://user-service:8002"
    group_service_url: str = "http://group-service:8003"
    calendar_service_url: str = "http://calendar-service:8004"
    ideas_service_url: str = "http://ideas-service:8005"
    voting_service_url: str = "http://voting-service:8006"
    recommendation_service_url: str = "http://recommendation-service:8007"
    notification_service_url: str = "http://notification-service:8008"
    telegram_service_url: str = "http://telegram-service:8009"
    scheduler_service_url: str = "http://scheduler-service:8010"

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None

    # External APIs
    ticketmaster_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None
    opentripmap_api_key: Optional[str] = None
    openweather_api_key: Optional[str] = None

    model_config = {"env_file": ".env", "case_sensitive": False}


def get_settings() -> Settings:
    return Settings()

"""Gateway configuration."""

from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """Gateway-specific settings."""

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
    meeting_service_url: str = "http://meeting-service:8011"

    # JWT
    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Upload
    upload_max_size: int = 10 * 1024 * 1024  # 10 MB
    upload_dir: str = "/uploads"

    # CORS
    cors_origins: str = "https://localhost,http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "case_sensitive": False}

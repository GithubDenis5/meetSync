from pydantic_settings import BaseSettings
from typing import Optional


class RecommendationSettings(BaseSettings):
    debug: bool = True
    redis_host: str = "redis"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    ticketmaster_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None
    opentripmap_api_key: Optional[str] = None
    openweather_api_key: Optional[str] = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"

    model_config = {"env_file": ".env", "case_sensitive": False}

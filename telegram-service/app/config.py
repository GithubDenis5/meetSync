from pydantic_settings import BaseSettings
from typing import Optional


class TelegramSettings(BaseSettings):
    debug: bool = True
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    service_port: int = 8009
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "meetsync"
    rabbitmq_password: str = "meetsync_rabbit_pass"

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"

    model_config = {"env_file": ".env", "case_sensitive": False}

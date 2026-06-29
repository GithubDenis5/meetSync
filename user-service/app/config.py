from pydantic_settings import BaseSettings


class UserSettings(BaseSettings):
    debug: bool = True
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "meetsync"
    postgres_user: str = "meetsync"
    postgres_password: str = "meetsync_secret_pass"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "meetsync"
    rabbitmq_password: str = "meetsync_rabbit_pass"

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "case_sensitive": False}

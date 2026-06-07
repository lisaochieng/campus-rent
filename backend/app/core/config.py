from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def sqlalchemy_postgres_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def driver_postgres_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    app_name: str = "CampusRent API"
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_db: str = "campusrent"
    postgres_user: str = "campusrent"
    postgres_password: str = "campusrent"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    redis_url: str = "redis://localhost:6379/0"
    opensearch_url: str = "http://localhost:9200"
    ingestion_api_key: str = "campusrent-local-dev-key"
    rentcast_api_key: str | None = None
    serpapi_api_key: str | None = None
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def postgres_dsn(self) -> str:
        if self.database_url:
            return sqlalchemy_postgres_url(self.database_url)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_driver_dsn(self) -> str:
        if self.database_url:
            return driver_postgres_url(self.database_url)
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

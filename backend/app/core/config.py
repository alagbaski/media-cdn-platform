"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API service."""

    app_name: str = "Media CDN Platform API"
    app_version: str = "1.0.0"
    service_name: str = "media-cdn-platform"
    environment: str = "development"

    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    api_prefix: str = "/api/v1"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"

    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        """Accept common deployment-style debug values."""
        if isinstance(value, bool):
            return value

        normalized = value.strip().lower()
        truthy = {"1", "true", "yes", "on", "debug", "development", "dev"}
        falsy = {"0", "false", "no", "off", "release", "prod", "production"}

        if normalized in truthy:
            return True
        if normalized in falsy:
            return False

        raise ValueError("DEBUG must be a boolean or a recognized mode string")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()

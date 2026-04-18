"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Detect if running in Docker by checking for /.dockerenv
IS_DOCKER = Path("/.dockerenv").exists()
REPO_ROOT_DIR = Path("/app") if IS_DOCKER else Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime configuration for the API service."""

    app_name: str = Field(validation_alias=AliasChoices("APP_NAME"))
    app_version: str = Field(validation_alias=AliasChoices("APP_VERSION"))
    service_name: str = Field(validation_alias=AliasChoices("SERVICE_NAME"))
    environment: str = Field(
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENVIRONMENT"),
    )

    debug: bool = Field(validation_alias=AliasChoices("DEBUG"))
    host: str = Field(validation_alias=AliasChoices("HOST"))
    port: int = Field(
        validation_alias=AliasChoices("BACKEND_PORT", "PORT"),
    )
    backend_upload_path: Path = Field(
        validation_alias=AliasChoices("BACKEND_UPLOAD_PATH", "UPLOAD_PATH"),
    )

    api_prefix: str = Field(
        default="/api/v1", validation_alias=AliasChoices("API_PREFIX")
    )
    docs_url: str | None = Field(
        default="/docs", validation_alias=AliasChoices("DOCS_URL")
    )
    redoc_url: str | None = Field(
        default="/redoc", validation_alias=AliasChoices("REDOC_URL")
    )
    openapi_url: str | None = Field(
        default="/openapi.json", validation_alias=AliasChoices("OPENAPI_URL")
    )

    minio_endpoint: str | None = Field(
        default=None, validation_alias=AliasChoices("MINIO_ENDPOINT")
    )
    minio_access_key: str | None = Field(
        default=None, validation_alias=AliasChoices("MINIO_ACCESS_KEY")
    )
    minio_secret_key: str | None = Field(
        default=None, validation_alias=AliasChoices("MINIO_SECRET_KEY")
    )
    minio_bucket: str | None = Field(
        default=None, validation_alias=AliasChoices("MINIO_BUCKET")
    )

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT_DIR / ".env" if not IS_DOCKER else None,
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

    @field_validator("backend_upload_path", mode="before")
    @classmethod
    def normalize_upload_path(cls, value: str | Path) -> Path:
        """Resolve relative upload paths against repository root."""
        path_value = Path(value)
        return path_value if path_value.is_absolute() else REPO_ROOT_DIR / path_value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()

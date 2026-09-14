"""
Application configuration.

All settings are read from environment variables. pydantic-settings handles
type coercion and validation. A single cached settings instance is returned
by get_settings() to avoid repeated env reads.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    CivicTrace application settings.

    Values are resolved in this order (highest priority first):
    1. Environment variables
    2. .env file (development only)
    3. Defaults declared below
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    environment: Literal["development", "staging", "production"] = "development"
    app_name: str = "civictrace-api"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    api_v1_prefix: str = "/api/v1"

    # Comma-separated in env vars; list in code.
    allowed_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        """Accept either a comma-separated string or a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    secret_key: str = "insecure-dev-secret-change-in-production"
    access_token_expire_minutes: int = 30

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    # Async DSN — used by SQLAlchemy async engine (asyncpg driver)
    database_url: str = (
        "postgresql+asyncpg://civictrace:civictrace@localhost:5432/civictrace"
    )

    # Sync DSN — used by Alembic only (psycopg v3 driver)
    database_url_sync: str = (
        "postgresql+psycopg://civictrace:civictrace@localhost:5432/civictrace"
    )

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ------------------------------------------------------------------
    # AI (Gemini)
    # ------------------------------------------------------------------
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")

    # ------------------------------------------------------------------
    # Storage (Supabase)
    # ------------------------------------------------------------------
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_storage_bucket: str = "evidence"

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    Use FastAPI's Depends(get_settings) in route handlers to allow
    easy overriding in tests via app.dependency_overrides.
    """
    return Settings()


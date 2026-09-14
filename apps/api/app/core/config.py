"""
Application configuration.

All settings are read from environment variables. pydantic-settings handles
type coercion and validation. A single cached settings instance is returned
by get_settings() to avoid repeated env reads.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, AnyUrl, Field, field_validator
from pathlib import Path
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
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
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
    allowed_origins: list[str] | str = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
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
    # AI Providers & Configuration
    # ------------------------------------------------------------------
    ai_primary_provider: str = Field(
        default="azure",
        validation_alias=AliasChoices("ai_primary_provider", "ai_provider"),
    )
    ai_fallback_provider: str = Field(
        default="gemini",
        validation_alias=AliasChoices("ai_fallback_provider"),
    )

    # Azure Computer Vision (Primary Visual)
    azure_ai_vision_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("azure_ai_vision_endpoint", "azure_vision_endpoint"),
    )
    azure_ai_vision_key: str = Field(
        default="",
        validation_alias=AliasChoices("azure_ai_vision_key", "azure_vision_key"),
    )

    # Azure AI Language (Citizen Problem Briefing Perception)
    azure_ai_language_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("azure_ai_language_endpoint", "azure_language_endpoint"),
    )
    azure_ai_language_key: str = Field(
        default="",
        validation_alias=AliasChoices("azure_ai_language_key", "azure_language_key"),
    )

    # Azure AI Speech (Speech-to-Text for Citizen Voice Briefing)
    azure_ai_speech_key: str = Field(
        default="",
        validation_alias=AliasChoices("azure_ai_speech_key", "azure_speech_key"),
    )
    azure_ai_speech_region: str = Field(
        default="eastus",
        validation_alias=AliasChoices("azure_ai_speech_region", "azure_speech_region"),
    )

    # Gemini (Fallback)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")

    @property
    def azure_vision_configured(self) -> bool:
        return bool(self.azure_ai_vision_endpoint and self.azure_ai_vision_key)

    @property
    def azure_language_configured(self) -> bool:
        return bool(self.azure_ai_language_endpoint and self.azure_ai_language_key)

    @property
    def azure_speech_configured(self) -> bool:
        return bool(self.azure_ai_speech_key and self.azure_ai_speech_region)

    # ------------------------------------------------------------------
    # Storage (Supabase)
    # ------------------------------------------------------------------
    supabase_url: str = Field(default="")
    supabase_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("supabase_secret_key", "supabase_key"),
    )
    supabase_storage_bucket: str = Field(
        default="evidence",
        validation_alias=AliasChoices("supabase_storage_bucket", "storage_bucket"),
    )

    @property
    def supabase_key(self) -> str:
        return self.supabase_secret_key

    @property
    def storage_bucket(self) -> str:
        return self.supabase_storage_bucket

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

"""
Tests for application configuration loading.
"""

import pytest

from app.core.config import Settings, get_settings


def test_settings_loads_defaults():
    """Settings must load successfully with default values."""
    settings = Settings(
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert settings.app_name == "civictrace-api"
    assert settings.environment == "development"
    assert settings.api_v1_prefix == "/api/v1"


def test_settings_allowed_origins_from_string():
    """ALLOWED_ORIGINS must be parseable from a comma-separated string."""
    settings = Settings(
        allowed_origins="http://localhost:3000,http://localhost:5173",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert "http://localhost:3000" in settings.allowed_origins
    assert "http://localhost:5173" in settings.allowed_origins


def test_settings_allowed_origins_from_list():
    """ALLOWED_ORIGINS must accept a list directly."""
    settings = Settings(
        allowed_origins=["http://localhost:3000"],
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert settings.allowed_origins == ["http://localhost:3000"]


def test_settings_environment_flags():
    """is_development and is_production flags must be mutually exclusive."""
    dev = Settings(
        environment="development",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert dev.is_development is True
    assert dev.is_production is False

    prod = Settings(
        environment="production",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert prod.is_production is True
    assert prod.is_development is False


def test_get_settings_returns_cached_instance():
    """get_settings() must return the same object on repeated calls."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_supabase_storage_config():
    """Supabase storage variables and aliases must be parsed cleanly."""
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_secret_key="dummy_secret_key",
        supabase_storage_bucket="evidence",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_secret_key == "dummy_secret_key"
    assert settings.supabase_key == "dummy_secret_key"
    assert settings.supabase_storage_bucket == "evidence"
    assert settings.storage_bucket == "evidence"


def test_settings_azure_ai_vision_config():
    """Azure AI Vision provider and credentials must be parsed cleanly."""
    settings = Settings(
        ai_primary_provider="azure",
        ai_fallback_provider="gemini",
        azure_ai_vision_endpoint="https://test.cognitiveservices.azure.com/",
        azure_ai_vision_key="dummy_azure_key",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )
    assert settings.ai_primary_provider == "azure"
    assert settings.ai_fallback_provider == "gemini"
    assert settings.azure_ai_vision_endpoint == "https://test.cognitiveservices.azure.com/"
    assert settings.azure_ai_vision_key == "dummy_azure_key"
    assert settings.azure_vision_configured is True

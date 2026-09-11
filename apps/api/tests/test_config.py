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

"""
pytest configuration and shared fixtures.

All fixtures in this file are automatically available to every test module
without explicit imports (pytest collects conftest.py automatically).

Key fixtures:
- event_loop:     Single shared asyncio event loop for the test session.
- app:            FastAPI application instance with test overrides applied.
- async_client:   httpx AsyncClient wired to the ASGI app (no real HTTP).
- db_session:     In-process async SQLAlchemy session for DB tests.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.main import create_app

# ---------------------------------------------------------------------------
# Test settings override
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = (
    "postgresql+asyncpg://civictrace:civictrace@localhost:5432/civictrace_test"
)


def get_test_settings() -> Settings:
    """Return settings configured for the test environment."""
    return Settings(
        environment="development",
        database_url=TEST_DATABASE_URL,
        database_url_sync=TEST_DATABASE_URL.replace("+asyncpg", "+psycopg"),
        secret_key="test-secret-key-not-for-production",
        log_level="WARNING",  # Suppress noise during tests.
        gemini_api_key="test-dummy-key-do-not-use"
    )


# ---------------------------------------------------------------------------
# Async event loop
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# In-memory test database (per test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_engine():
    """Create an async engine targeting the test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a clean async session for each test.

    Creates all tables before the test and drops them after.
    This keeps tests fully isolated from each other.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# FastAPI test application
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_app(test_engine):
    """
    Return a FastAPI app instance with test dependency overrides:
    - get_settings → test settings
    - get_db       → session backed by the test database
    """
    application = create_app()

    # Override settings.
    application.dependency_overrides[get_settings] = get_test_settings

    # Override DB session factory.
    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db] = override_get_db

    return application


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an httpx AsyncClient wired to the test ASGI app.

    No real HTTP connections are made — requests are dispatched
    directly into the FastAPI ASGI callable.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as client:
        yield client

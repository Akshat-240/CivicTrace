"""
Async SQLAlchemy engine, session factory, and base model.

Design principles:
- No global mutable session objects.
- Sessions are created per-request via get_db() dependency and closed
  on request completion (see api/dependencies.py).
- The async engine is a module-level singleton but is stateless between
  requests — the connection pool handles concurrency.
- All ORM models inherit from Base, which carries common audit columns.
"""

from collections.abc import AsyncGenerator
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import DateTime, func
import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _build_engine(settings: Any = None) -> AsyncEngine:
    if settings is None:
        settings = get_settings()

    connect_args: dict[str, Any] = {}
    if "asyncpg" in settings.database_url:
        # asyncpg requires server_settings for PostGIS-aware sessions.
        connect_args["server_settings"] = {"application_name": settings.app_name}

    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,          # Verify connections before checkout.
        echo=settings.is_development, # Log SQL only in development.
        connect_args=connect_args,
    )


engine: AsyncEngine = _build_engine()

# Session factory — produces per-request sessions via get_db().
AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Avoid lazy-load errors after commit in async context.
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Base ORM model
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """
    Declarative base for all ORM models.

    All concrete models inherit from this class, which provides:
    - UUID primary key
    - created_at / updated_at audit timestamps
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Session dependency helper
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a transactional async session for the current request.

    Usage in route handlers via FastAPI dependency injection:
        async def my_route(db: AsyncSession = Depends(get_db)): ...

    The session is committed on success and rolled back on any exception,
    then closed regardless of outcome.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Startup health check
# ---------------------------------------------------------------------------


async def check_db_connection() -> None:
    """
    Verify that the database is reachable.

    Called once at application startup. Raises ServiceUnavailableError
    if the database cannot be reached so the process fails fast rather
    than serving 500s on every request.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_health_check_passed")
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc))
        raise ServiceUnavailableError(
            "Database is not reachable. Check DATABASE_URL and ensure "
            "PostgreSQL is running."
        ) from exc

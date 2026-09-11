"""
CivicTrace API — Application entry point.

This module is the application factory. It creates the FastAPI instance,
registers all middleware, mounts routers, and sets up lifespan events.
Business logic lives entirely in the service layer — never here.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health
from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import (
    CivicTraceError,
    civictrace_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from fastapi.exceptions import RequestValidationError

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown.

    Startup:  configure logging, verify DB connectivity.
    Shutdown: dispose connection pool cleanly.
    """
    settings = get_settings()
    configure_logging(settings.log_level, settings.environment)

    logger.info(
        "civictrace_api_starting",
        environment=settings.environment,
        version=settings.app_version,
    )

    # Verify the database is reachable before accepting traffic.
    from app.core.database import check_db_connection

    await check_db_connection()
    logger.info("database_connection_verified")

    yield

    # Graceful shutdown: dispose the async engine pool.
    await engine.dispose()
    logger.info("civictrace_api_stopped")


def create_app() -> FastAPI:
    """Application factory — returns a configured FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="CivicTrace API",
        description="Civic issue intelligence and accountability platform.",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------
    app.add_exception_handler(CivicTraceError, civictrace_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health.router, tags=["system"])

    # Domain routers will be added here as features are built out.
    from app.api.routes import incidents
    app.include_router(incidents.router, prefix=settings.api_v1_prefix)
    # app.include_router(evidence.router,  prefix=settings.api_v1_prefix)

    return app


# The ASGI application instance used by uvicorn / gunicorn.
app = create_app()

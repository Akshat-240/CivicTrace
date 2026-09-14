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


import asyncio

async def run_sla_poller_loop():
    from app.core.database import AsyncSessionFactory as async_session_maker
    from app.services.sla_poller import SLAPoller

    # Run every 5 minutes in production, but let's make it configurable or standard interval.
    # 5 minutes is 300 seconds.
    while True:
        try:
            async with async_session_maker() as session:
                poller = SLAPoller(session)
                summary = await poller.evaluate_all_active_slas()
                logger.debug("sla_poller_run", summary=summary)
        except Exception as e:
            logger.error("sla_poller_fatal_error", error=str(e))

        await asyncio.sleep(300)

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

    # Start the background SLA poller
    poller_task = asyncio.create_task(run_sla_poller_loop())

    yield

    # Graceful shutdown: dispose the async engine pool.
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass

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
    from app.api.routes import incidents, system, auth, ai, worker
    app.include_router(incidents.router, prefix=settings.api_v1_prefix)
    app.include_router(system.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(ai.router, prefix=settings.api_v1_prefix)
    app.include_router(worker.router, prefix=settings.api_v1_prefix + "/worker", tags=["worker"])
    # app.include_router(evidence.router,  prefix=settings.api_v1_prefix)

    return app


# The ASGI application instance used by uvicorn / gunicorn.
app = create_app()


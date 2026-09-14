"""
Structured logging configuration.

Uses structlog with JSON output in staging/production and
human-readable console output in development.

All log records include a correlation_id that is injected per-request
via middleware, making it possible to trace any request across the full
log stream.
"""

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

# Per-request correlation ID. Set by the request middleware.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current request's correlation ID."""
    return _correlation_id.get() or str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Bind a correlation ID to the current async context."""
    _correlation_id.set(correlation_id)


def _add_correlation_id(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """structlog processor that injects the correlation ID."""
    cid = _correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def configure_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """
    Configure structlog and the standard library logging integration.

    Call once at application startup. Safe to call multiple times
    (subsequent calls are no-ops due to basicConfig behaviour).
    """
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if environment == "development":
        # Pretty, colourised output for local development.
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        # Machine-parseable JSON for staging/production log aggregators.
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *shared_processors,
            renderer,
        ]
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Only add our handler if one hasn't been added already.
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(log_level_int)

    # Quiet noisy libraries.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

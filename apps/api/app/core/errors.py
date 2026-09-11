"""
Global error handling.

Defines the domain exception hierarchy and FastAPI exception handlers
that translate exceptions into a consistent JSON error envelope:

    {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Incident inc_123 not found.",
            "detail": null
        }
    }

Route handlers should raise CivicTraceError subclasses.
They must NEVER leak raw SQLAlchemy or third-party exceptions to callers.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain exception hierarchy
# ---------------------------------------------------------------------------


class CivicTraceError(Exception):
    """Base exception for all application-level errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        detail: Any = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "detail": self.detail,
            }
        }


class NotFoundError(CivicTraceError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(CivicTraceError):
    """Raised when an operation conflicts with existing state."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "The request conflicts with existing data."


class ValidationError(CivicTraceError):
    """Raised when domain-level validation fails (not schema validation)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "VALIDATION_ERROR"
    message = "The request data is invalid."


class UnauthorizedError(CivicTraceError):
    """Raised when a request is not authenticated."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication is required."


class ForbiddenError(CivicTraceError):
    """Raised when a request is authenticated but not authorised."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class ServiceUnavailableError(CivicTraceError):
    """Raised when a downstream service (DB, AI, GIS) is unreachable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "A required service is temporarily unavailable."


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------


async def civictrace_exception_handler(
    request: Request,
    exc: CivicTraceError,
) -> JSONResponse:
    """Handle all CivicTraceError subclasses."""
    logger.warning(
        "civictrace_error",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Translate Pydantic/FastAPI validation errors into the standard envelope."""
    logger.info(
        "request_validation_error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "detail": exc.errors(),
            }
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all for any unhandled exceptions.

    Logs the full traceback but returns a generic message to the caller
    to avoid leaking internal details.
    """
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "detail": None,
            }
        },
    )

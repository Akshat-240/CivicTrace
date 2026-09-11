"""
Shared Pydantic base configuration and common schema types.

All schemas in CivicTrace inherit from CivicBaseModel, which sets:
- model_config with from_attributes=True (ORM mode)
- alias_generator and populate_by_name for camelCase/snake_case flexibility
- json_schema_extra for OpenAPI documentation hints

Common reusable types (UUIDs, pagination, error envelopes) live here too.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class CivicBaseModel(BaseModel):
    """
    Base Pydantic model for all CivicTrace schemas.

    - from_attributes=True: SQLAlchemy ORM instances can be passed directly
      to response schemas.
    - Timestamps are always UTC-aware.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Common response wrappers
# ---------------------------------------------------------------------------


class PaginatedResponse(CivicBaseModel, Generic[T]):
    """Standard paginated list response."""

    data: list[T]
    total: int
    page: int
    page_size: int


class ErrorDetail(CivicBaseModel):
    """Single error entry."""

    code: str
    message: str
    detail: Optional[object] = None


class ErrorResponse(CivicBaseModel):
    """Standard error envelope returned by all error handlers."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Common field types (reuse across schemas)
# ---------------------------------------------------------------------------


class AuditFields(CivicBaseModel):
    """Read-only audit timestamps inherited by all response schemas."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

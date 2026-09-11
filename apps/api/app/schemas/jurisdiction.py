"""
Authority and Jurisdiction Pydantic schemas.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.schemas.base import AuditFields, CivicBaseModel


class AuthorityResponse(AuditFields):
    """Authority record as returned by the API."""

    name: str
    short_code: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool
    sla_hours_low: int
    sla_hours_medium: int
    sla_hours_high: int
    sla_hours_critical: int


class JurisdictionResponse(AuditFields):
    """Jurisdiction record as returned by the API (boundary not exposed)."""

    name: str
    code: str
    description: Optional[str] = None
    authority: Optional[AuthorityResponse] = None

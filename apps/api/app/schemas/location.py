"""
Location Pydantic schemas.

Separate schemas for:
- LocationCreate: inbound data (lat/lng required, everything else optional)
- LocationResponse: outbound representation (no geometry column — serialised
  as lat/lng pair for API consumers; raw WKB geometry is not exposed)
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import AuditFields, CivicBaseModel


class LocationCreate(CivicBaseModel):
    """Payload for creating a new location from submitted evidence."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS-84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS-84 longitude")
    accuracy_meters: Optional[float] = Field(None, ge=0.0)
    address_raw: Optional[str] = None


class LocationResponse(AuditFields):
    """Location as returned by the API — geometry serialised as coordinates."""

    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    address_raw: Optional[str] = None
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None

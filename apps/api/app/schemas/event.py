"""
Incident Event Pydantic schemas.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.models.enums import EventType
from app.schemas.base import AuditFields


class EventResponse(AuditFields):
    """Event record as returned by the API."""

    incident_id: uuid.UUID
    event_type: EventType
    actor: str
    summary: Optional[str] = None
    detail: Optional[str] = None
    payload: Optional[dict] = None

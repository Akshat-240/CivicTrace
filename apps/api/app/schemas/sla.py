"""
SLA and SLA Rule Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.enums import AccountabilityState
from app.schemas.base import AuditFields, CivicBaseModel


class SLAResponse(AuditFields):
    """SLA and accountability state as returned by the API."""

    state: AccountabilityState
    started_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    overdue_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    is_escalation_eligible: bool
    escalation_note: Optional[str] = None


class SLARuleCreate(CivicBaseModel):
    """Payload to create an SLA rule for an authority + issue_type."""

    authority_id: uuid.UUID
    issue_type: str = Field(..., max_length=50)
    resolution_hours: int = Field(..., gt=0)
    escalation_grace_hours: int = Field(default=72, ge=0)
    is_active: bool = True


class SLARuleResponse(AuditFields):
    """SLA rule configuration representation."""

    authority_id: uuid.UUID
    issue_type: str
    resolution_hours: int
    escalation_grace_hours: int
    is_active: bool

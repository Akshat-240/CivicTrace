"""
Priority, SLA, and Verification Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.models.enums import (
    AccountabilityState,
    PriorityLevel,
    SeverityLevel,
    VerificationResult,
)
from app.schemas.base import AuditFields, CivicBaseModel


class PriorityResponse(AuditFields):
    """Priority record as returned by the API."""

    severity: Optional[SeverityLevel] = None
    safety_risk: bool
    persistence_score: Optional[float] = None
    final_priority: Optional[PriorityLevel] = None
    explanation: Optional[str] = None


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


class VerificationResponse(AuditFields):
    """Verification record as returned by the API."""

    result: Optional[VerificationResult] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    before_evidence_id: Optional[uuid.UUID] = None
    after_evidence_id: Optional[uuid.UUID] = None


class VerificationSubmit(CivicBaseModel):
    """Payload to submit a verification result for an incident."""

    result: VerificationResult
    explanation: Optional[str] = None
    after_evidence_id: Optional[uuid.UUID] = None
    verified_by: Optional[str] = None

"""
Verification Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.models.enums import VerificationResult
from app.schemas.base import AuditFields, CivicBaseModel


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

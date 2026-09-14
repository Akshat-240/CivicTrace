"""
Evidence Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.models.enums import EvidenceStatus, EvidenceType
from app.schemas.base import AuditFields, CivicBaseModel
from app.schemas.location import LocationCreate, LocationResponse


class EvidenceSubmit(CivicBaseModel):
    """
    Payload submitted by a reporter when capturing new evidence.

    The storage_key is set server-side after the file is stored — the
    client submits a pre-signed upload result or a URL.
    """

    evidence_type: EvidenceType
    description: Optional[str] = Field(None, max_length=5000)
    occurred_at: Optional[datetime] = None
    location: Optional[LocationCreate] = None
    # Optional: client may provide the storage key if using direct-upload
    storage_key: Optional[str] = Field(None, max_length=1000)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size_bytes: Optional[int] = Field(None, gt=0)


class EvidenceResponse(AuditFields):
    """Evidence item as returned by the API."""

    evidence_type: EvidenceType
    status: EvidenceStatus
    incident_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    # Note: storage_key is NOT exposed — only a signed URL would be
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_severity_raw: Optional[str] = None
    ai_safety_risk: Optional[bool] = None
    ai_ambiguity_flag: bool = False
    ai_ambiguity_reason: Optional[str] = None
    ai_perception_payload: Optional[dict[str, Any]] = None
    is_verification_evidence: bool = False
    location: Optional[LocationResponse] = None

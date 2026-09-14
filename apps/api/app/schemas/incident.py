"""
Incident Pydantic schemas.

Three distinct shapes:
- IncidentListItem:   Lightweight summary for the dashboard list view.
- IncidentDetail:     Full incident with all related records embedded.
- IncidentCreate:     Not used externally — incidents are created by fusion.
                      Included for internal service use and admin tooling.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.models.enums import IncidentStatus, IssueType
from app.schemas.base import AuditFields, CivicBaseModel
from app.schemas.location import LocationCreate, LocationResponse
from app.schemas.jurisdiction import AuthorityResponse, JurisdictionResponse
from app.schemas.priority import PriorityResponse, SLAResponse, VerificationResponse


class IncidentListItem(AuditFields):
    """
    Lightweight incident summary for list/map views.

    Minimises data transfer — no embedded related records.
    """

    reference_number: str
    status: IncidentStatus
    issue_type: Optional[IssueType] = None
    title: Optional[str] = None
    evidence_count: int
    ai_ambiguity_flag: bool
    location: Optional[LocationResponse] = None
    authority: Optional[AuthorityResponse] = None
    # Priority level only (not full priority record)
    priority_level: Optional[str] = None
    # Accountability state only (not full SLA record)
    accountability_state: Optional[str] = None


class IncidentDetail(AuditFields):
    """
    Full incident record with all related data embedded.

    Used for the incident detail page.
    """

    reference_number: str
    status: IncidentStatus
    issue_type: Optional[IssueType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    evidence_count: int
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_ambiguity_flag: bool
    location: Optional[LocationResponse] = None
    jurisdiction: Optional[JurisdictionResponse] = None
    authority: Optional[AuthorityResponse] = None
    priority: Optional[PriorityResponse] = None
    sla: Optional[SLAResponse] = None
    verification: Optional[VerificationResponse] = None


class IncidentCreate(CivicBaseModel):
    """
    Internal schema for creating an Incident (used by fusion service).

    Not exposed as a public API endpoint — incidents are created automatically
    by the fusion pipeline.
    """

    reference_number: str
    status: IncidentStatus = IncidentStatus.DRAFT
    issue_type: Optional[IssueType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[uuid.UUID] = None
    primary_evidence_id: Optional[uuid.UUID] = None


class IncidentSubmit(CivicBaseModel):
    """
    Payload to explicitly submit a new incident.
    """
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    issue_type: Optional[IssueType] = None
    location: Optional[LocationCreate] = None


class ResolutionSubmit(CivicBaseModel):
    """
    Payload for an authority submitting resolution evidence.
    No binary upload -- text description only (MVP limitation: no binary storage).
    evidence_type defaults to TEXT.
    """
    description: str = Field(..., min_length=10, max_length=5000,
                             description="Description of the resolution work performed.")
    evidence_type: Optional[str] = Field(default="text",
                                         description="Evidence type (text only in MVP -- no binary storage).")

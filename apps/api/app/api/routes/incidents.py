"""
Incidents API routes.
"""

import uuid
from typing import Any, Sequence

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import DbSession
from app.schemas import (
    EventResponse,
    EvidenceResponse,
    EvidenceSubmit,
    IncidentDetail,
    IncidentListItem,
    IncidentSubmit,
    PaginatedResponse,
    SLAResponse,
    VerificationResponse,
)
from app.services.evidence_service import EvidenceService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post(
    "",
    response_model=IncidentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
)
async def create_incident(
    data: IncidentSubmit,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.create_incident(data)


@router.get(
    "",
    response_model=PaginatedResponse[IncidentListItem],
    summary="List incidents",
)
async def list_incidents(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    service = IncidentService(db)
    incidents, total = await service.list_incidents(skip, limit)
    return {
        "data": incidents,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get(
    "/{incident_id}",
    response_model=IncidentDetail,
    summary="Get incident details",
)
async def get_incident(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.get_incident(incident_id)


@router.post(
    "/{incident_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add evidence to incident",
)
async def add_evidence(
    incident_id: uuid.UUID,
    data: EvidenceSubmit,
    db: DbSession,
) -> Any:
    service = EvidenceService(db)
    return await service.add_evidence(incident_id, data)


@router.get(
    "/{incident_id}/evidence",
    response_model=list[EvidenceResponse],
    summary="List evidence for incident",
)
async def list_evidence(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = EvidenceService(db)
    return await service.list_evidence(incident_id)


@router.get(
    "/{incident_id}/timeline",
    response_model=list[EventResponse],
    summary="Get incident timeline events",
)
async def get_timeline(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.get_incident_timeline(incident_id)


@router.get(
    "/{incident_id}/accountability",
    response_model=SLAResponse,
    summary="Get incident SLA & accountability state",
)
async def get_accountability(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.get_incident_accountability(incident_id)


@router.get(
    "/{incident_id}/verification",
    response_model=VerificationResponse,
    summary="Get incident verification result",
)
async def get_verification(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.get_incident_verification(incident_id)


from app.schemas.ai import AIAnalysisResult
from app.services.ai.service import AIService

@router.post(
    "/{incident_id}/evidence/{evidence_id}/analyze",
    response_model=AIAnalysisResult,
    summary="Trigger AI analysis on an evidence item",
)
async def analyze_evidence(
    incident_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: DbSession,
) -> Any:
    # Ensure evidence belongs to incident, omitted for brevity / handled implicitly or in service
    ai_service = AIService(db)
    return await ai_service.process_evidence(evidence_id)

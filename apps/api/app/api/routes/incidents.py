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
    # Ensure evidence belongs to incident
    ai_service = AIService(db)
    return await ai_service.process_evidence(evidence_id)

@router.post(
    "/{incident_id}/assign-jurisdiction",
    response_model=IncidentDetail,
    summary="Trigger GIS jurisdiction assignment for an incident",
)
async def assign_jurisdiction(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.assign_jurisdiction(incident_id)

@router.post(
    "/{incident_id}/prioritize",
    response_model=Any,
    summary="Compute final incident priority using evidence aggregation",
)
async def compute_priority(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    from app.services.priority_service import PriorityService
    service = PriorityService(db)
    # Returning the dictionary representing Priority model for simplicity
    p = await service.compute_priority(incident_id)
    return {
        "final_priority": p.final_priority,
        "explanation": p.explanation,
        "safety_risk": p.safety_risk,
        "severity": p.severity,
        "persistence_score": p.persistence_score
    }

@router.post(
    "/{incident_id}/start-sla",
    response_model=Any,
    summary="Start SLA clock for a prioritized incident",
)
async def start_sla(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    from app.services.sla_service import AccountabilityService
    service = AccountabilityService(db)
    sla_record = await service.start_sla(incident_id)
    return {
        "state": sla_record.state,
        "started_at": sla_record.started_at,
        "due_at": sla_record.due_at,
    }

@router.post(
    "/{incident_id}/evaluate-sla",
    response_model=Any,
    summary="Evaluate and transition SLA state machine",
)
async def evaluate_sla(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    from app.services.sla_service import AccountabilityService
    service = AccountabilityService(db)
    sla_record = await service.evaluate_sla(incident_id)
    return {
        "state": sla_record.state,
        "overdue_at": sla_record.overdue_at,
        "is_escalation_eligible": sla_record.is_escalation_eligible,
    }

@router.post(
    "/{incident_id}/verify-resolution",
    response_model=Any,
    summary="Execute evidence-based resolution verification",
)
async def verify_resolution(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    from app.services.verification_service import VerificationService
    service = VerificationService(db)
    record = await service.verify_resolution(incident_id)
    return {
        "result": record.result,
        "explanation": record.explanation,
        "confidence": record.confidence,
        "verified_at": record.verified_at,
    }

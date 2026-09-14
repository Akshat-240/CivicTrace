"""
Incidents API routes.
"""

import uuid
from typing import Any, Optional, Sequence

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import DbSession, get_current_user
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
    current_user = Depends(get_current_user),
) -> Any:
    service = IncidentService(db)
    return await service.create_incident(data, citizen_id=current_user.id)


@router.get(
    "",
    response_model=PaginatedResponse[IncidentListItem],
    summary="List incidents",
)
async def list_incidents(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    citizen_id: Optional[str] = Query(None, description="Filter incidents by authenticated citizen ID"),
    authority_id: Optional[str] = Query(None, description="Filter incidents by assigned authority ID"),
) -> Any:
    service = IncidentService(db)
    incidents, total = await service.list_incidents(skip, limit, citizen_id=citizen_id, authority_id=authority_id)
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
    incident_id: str,
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


from fastapi import File, Form, UploadFile, HTTPException

@router.post(
    "/{incident_id}/evidence/upload",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload binary evidence to incident",
)
async def upload_evidence(
    incident_id: uuid.UUID,
    db: DbSession,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    accuracy_meters: Optional[float] = Form(None),
    address_raw: Optional[str] = Form(None),
) -> Any:
    service = EvidenceService(db)
    content = await file.read()
    from app.core.errors import ValidationError
    if not content:
        raise ValidationError("File content is empty")
        
    try:
        return await service.upload_evidence(
            incident_id=incident_id,
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            description=description,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            address_raw=address_raw,
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        if "maximum limit" in str(e) or "Unsupported MIME type" in str(e) or "VALIDATION_ERROR" in str(e):
            raise HTTPException(
                status_code=422,
                detail={"code": "VALIDATION_ERROR", "message": str(e)}
            )
        if "storage" in str(e).lower() or isinstance(e, RuntimeError):
            raise HTTPException(
                status_code=503,
                detail={"code": "SERVICE_UNAVAILABLE", "message": str(e)}
            )
        if "state and cannot accept" in str(e):
            raise HTTPException(
                status_code=409,
                detail={"code": "CONFLICT", "message": str(e)}
            )
        raise e

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
    incident_id: str,
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
    incident_id: str,
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
    incident_id: str,
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


@router.post(
    "/{incident_id}/submit-resolution",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit resolution evidence (ACTIVE -> UNDER_REVIEW)",
)
async def submit_resolution(
    incident_id: uuid.UUID,
    data: "ResolutionSubmit",
    db: DbSession,
) -> Any:
    """
    Authority submits resolution evidence for an ACTIVE incident.
    Moves incident to UNDER_REVIEW. Text evidence only (no binary storage in MVP).
    """
    from app.services.verification_service import VerificationService
    from app.schemas import ResolutionSubmit
    from app.models.enums import EvidenceType
    service = VerificationService(db)
    return await service.submit_resolution(
        incident_id=incident_id,
        description=data.description,
        evidence_type=EvidenceType.TEXT,
    )


@router.post(
    "/{incident_id}/human-verify",
    response_model=VerificationResponse,
    summary="Human reviewer makes a verification decision (UNDER_REVIEW required)",
)
async def human_verify(
    incident_id: uuid.UUID,
    data: "VerificationSubmit",
    db: DbSession,
) -> Any:
    """
    Human reviewer explicitly sets a VerificationResult.
    Only FULLY_RESOLVED transitions incident to RESOLVED.
    Requires resolution evidence to exist (cannot approve without evidence).
    """
    from app.services.verification_service import VerificationService
    service = VerificationService(db)
    return await service.human_verify(
        incident_id=incident_id,
        result=data.result,
        explanation=data.explanation,
        verified_by=data.verified_by,
    )


@router.post(
    "/{incident_id}/close",
    response_model=IncidentDetail,
    summary="Close a RESOLVED incident (backend-guarded)",
)
async def close_incident(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    """
    Explicitly closes a RESOLVED incident. Only RESOLVED -> CLOSED is allowed.
    All other statuses are rejected with 409 Conflict.
    """
    service = IncidentService(db)
    return await service.close_incident(incident_id)
@router.get(
    "/{incident_id}/intelligence-report",
    response_model=Any,
    summary="Get the structured CivicTrace Intelligence Report for an incident",
)
async def get_intelligence_report(
    incident_id: uuid.UUID,
    db: DbSession,
) -> Any:
    service = IncidentService(db)
    return await service.generate_intelligence_report(incident_id)

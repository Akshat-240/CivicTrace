from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import DbSession, get_current_worker
from app.models.incident import Incident
from app.models.evidence import Evidence
from app.models.worker_profile import WorkerProfile
from app.models.enums import WorkerTaskStatus, EvidencePhase, IncidentStatus, EvidenceType
from app.services.storage_service import StorageService
from app.services.evidence_service import EvidenceService
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

# Schema for updating status
class WorkerStatusUpdate(BaseModel):
    status: WorkerTaskStatus

class WorkerTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reference_number: str | None = None
    title: str | None = None
    description: str | None = None
    status: str
    worker_status: WorkerTaskStatus | None = None
    priority: str | None = None
    due_at: datetime | None = None

    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None

class WorkerTaskDetailResponse(WorkerTaskResponse):
    before_evidence_url: str | None = None

@router.get("/tasks", response_model=List[WorkerTaskResponse])
async def get_worker_tasks(
    db: DbSession,
    worker: WorkerProfile = Depends(get_current_worker)
):
    stmt = (
        select(Incident)
        .where(Incident.assigned_worker_id == worker.id)
        .where(Incident.status.in_([IncidentStatus.ACTIVE.value, IncidentStatus.UNDER_REVIEW.value, IncidentStatus.ACTIVE, IncidentStatus.UNDER_REVIEW]))
        .options(selectinload(Incident.location))
    )
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    tasks = []
    for inc in incidents:
        tasks.append(WorkerTaskResponse(
            id=inc.id,
            reference_number=inc.reference_number,
            title=inc.title,
            description=inc.description,
            status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            worker_status=inc.worker_status,
            priority=inc.priority_level,
            due_at=None,
            latitude=inc.location.latitude if inc.location else None,
            longitude=inc.location.longitude if inc.location else None,
            address=inc.location.address if inc.location else None
        ))
    return tasks

@router.get("/tasks/{incident_id}", response_model=WorkerTaskDetailResponse)
async def get_worker_task_detail(
    incident_id: uuid.UUID,
    db: DbSession,
    worker: WorkerProfile = Depends(get_current_worker)
):
    stmt = (
        select(Incident)
        .where(Incident.id == incident_id)
        .where(Incident.assigned_worker_id == worker.id)
        .where(Incident.authority_id == worker.authority_id)
        .options(
            selectinload(Incident.location),
            selectinload(Incident.evidence_items)
        )
    )
    result = await db.execute(stmt)
    inc = result.scalar_one_or_none()

    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found or not assigned to worker")

    before_evidence_url = None
    for ev in inc.evidence_items:
        if ev.evidence_phase == EvidencePhase.BEFORE:
            storage_service = StorageService()
            before_evidence_url = await storage_service.create_signed_url(ev.storage_key)
            break

    return WorkerTaskDetailResponse(
        id=inc.id,
        reference_number=inc.reference_number,
        title=inc.title,
        description=inc.description,
        status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        worker_status=inc.worker_status,
        priority=inc.priority_level,
        due_at=None,
        latitude=inc.location.latitude if inc.location else None,
        longitude=inc.location.longitude if inc.location else None,
        address=inc.location.address if inc.location else None,
        before_evidence_url=before_evidence_url
    )

@router.patch("/tasks/{incident_id}/status")
async def update_task_status(
    incident_id: uuid.UUID,
    payload: WorkerStatusUpdate,
    db: DbSession,
    worker: WorkerProfile = Depends(get_current_worker)
):
    if payload.status == WorkerTaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot manually set status to COMPLETED. Use resolution submission."
        )

    stmt = (select(Incident).where(Incident.id == incident_id)
        .where(Incident.assigned_worker_id == worker.id)
        .where(Incident.authority_id == worker.authority_id)
    )
    result = await db.execute(stmt)
    inc = result.scalar_one_or_none()

    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found or not assigned to worker")

    valid_transitions = {
        WorkerTaskStatus.ASSIGNED: [WorkerTaskStatus.ACCEPTED],
        WorkerTaskStatus.ACCEPTED: [WorkerTaskStatus.ON_THE_WAY],
        WorkerTaskStatus.ON_THE_WAY: [WorkerTaskStatus.AT_LOCATION],
        WorkerTaskStatus.AT_LOCATION: [WorkerTaskStatus.IN_PROGRESS],
        WorkerTaskStatus.IN_PROGRESS: [WorkerTaskStatus.COMPLETED],
    }

    current = inc.worker_status
    if payload.status not in valid_transitions.get(current, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {current} to {payload.status}"
        )

    inc.worker_status = payload.status
    await db.commit()
    return {"message": "Status updated successfully", "worker_status": inc.worker_status}

@router.post("/tasks/{incident_id}/submit-resolution")
async def submit_resolution(
    incident_id: uuid.UUID,
    db: DbSession,
    file: UploadFile = File(...),
    notes: str = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    capture_timestamp: str = Form(None),
    worker: WorkerProfile = Depends(get_current_worker)
):
    stmt = (select(Incident).where(Incident.id == incident_id)
        .where(Incident.assigned_worker_id == worker.id)
        .where(Incident.authority_id == worker.authority_id)
    )
    result = await db.execute(stmt)
    inc = result.scalar_one_or_none()

    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found or not assigned to worker")

    if inc.worker_status != WorkerTaskStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Cannot submit resolution from current status. Must be IN_PROGRESS.")

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "video/mp4"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="Worker GPS coordinates are required for resolution evidence.")
    if not capture_timestamp:
        raise HTTPException(status_code=400, detail="Capture timestamp is required for resolution evidence.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    evidence_service = EvidenceService(db)

    dt_occurred = None
    if capture_timestamp:
        try:
            from dateutil.parser import parse
            dt_occurred = parse(capture_timestamp)
        except Exception:
            pass

    mime = file.content_type or ""

    try:
        evidence = await evidence_service.upload_evidence(
            incident_id=incident_id,
            file_content=content,
            filename=file.filename or "after_evidence",
            content_type=mime,
            description=notes,
            occurred_at=dt_occurred,
            latitude=latitude,
            longitude=longitude,
            evidence_phase=EvidencePhase.AFTER
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Reload incident and update statuses
    stmt = select(Incident).where(Incident.id == incident_id)
    inc = (await db.execute(stmt)).scalar_one()

    inc.worker_status = WorkerTaskStatus.COMPLETED
    inc.status = IncidentStatus.UNDER_REVIEW

    # Store notes in fusion metadata or completion notes
    metadata = dict(inc.fusion_metadata or {})
    metadata["completion_notes"] = notes
    inc.fusion_metadata = metadata

    await db.commit()

    return {"message": "Resolution submitted successfully", "evidence_id": evidence.id}







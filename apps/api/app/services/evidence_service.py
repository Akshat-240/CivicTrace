"""
Evidence business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CivicTraceError, ConflictError, ServiceUnavailableError, ValidationError
from app.models.enums import EventType, EvidenceStatus, EvidenceType, IncidentStatus
from app.models.event import IncidentEvent
from app.models.evidence import Evidence
from app.models.location import Location
from app.repositories.event_repo import EventRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.evidence import EvidenceSubmit
from app.services.incident_service import IncidentService
from app.services.storage_service import StorageService

logger = structlog.get_logger(__name__)


class EvidenceService:
    def __init__(
        self,
        session: AsyncSession,
        storage_service: Optional[StorageService] = None,
    ):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        self.event_repo = EventRepository(session)
        self.incident_service = IncidentService(session)
        self.storage_service = storage_service or StorageService()

    async def add_evidence(
        self, incident_id: uuid.UUID, data: EvidenceSubmit
    ) -> Evidence:
        """
        Adds evidence metadata to an existing incident.
        Sets status to PENDING (awaiting perception).
        """
        # Ensure incident exists
        incident = await self.incident_service.get_incident(incident_id)

        # Check incident state
        status_val = incident.status.value if hasattr(incident.status, "value") else str(incident.status)
        if status_val in (IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value, IncidentStatus.INVALID.value):
            raise ConflictError(
                f"Incident {incident_id} is in '{status_val}' state and cannot accept new evidence."
            )

        # Handle location
        loc = None
        if data.location:
            loc = Location(
                latitude=data.location.latitude,
                longitude=data.location.longitude,
                accuracy_meters=data.location.accuracy_meters,
                address_raw=data.location.address_raw,
            )
            self.session.add(loc)
            await self.session.flush()

        evidence = Evidence(
            incident_id=incident_id,
            evidence_type=data.evidence_type,
            status=EvidenceStatus.PENDING,
            description=data.description,
            occurred_at=data.occurred_at,
            location_id=loc.id if loc else None,
            storage_key=data.storage_key,
            mime_type=data.mime_type,
            file_size_bytes=data.file_size_bytes,
        )
        await self.evidence_repo.create(evidence)

        # Update incident evidence count
        incident.evidence_count += 1

        # Add timeline event
        event = IncidentEvent(
            incident_id=incident_id,
            event_type=EventType.EVIDENCE_SUBMITTED,
            actor="user",
            summary=f"New {data.evidence_type.value} evidence submitted",
            payload={"evidence_id": str(evidence.id)},
        )
        await self.event_repo.create(event)

        return evidence

    async def upload_evidence(
        self,
        incident_id: uuid.UUID,
        file_content: bytes,
        filename: str,
        content_type: str,
        description: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy_meters: Optional[float] = None,
        address_raw: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
    ) -> Evidence:
        """
        Validates, uploads file to private storage, and records Evidence row.
        Executes compensation deletion on storage if DB insertion fails.
        """
        # 1. Verify incident exists
        incident = await self.incident_service.get_incident(incident_id)

        # 2. Verify incident lifecycle state
        status_val = incident.status.value if hasattr(incident.status, "value") else str(incident.status)
        if status_val in (IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value, IncidentStatus.INVALID.value):
            raise ConflictError(
                f"Incident {incident_id} is in '{status_val}' state and cannot accept new evidence."
            )

        # 3. Validate file payload (size, mime, non-empty)
        self.storage_service.validate_file(file_content, content_type)

        # 4. Validate location coordinates if provided
        loc = None
        if latitude is not None or longitude is not None:
            if latitude is None or longitude is None:
                raise ValidationError("Both latitude and longitude must be provided when specifying location.")
            if not (-90.0 <= latitude <= 90.0):
                raise ValidationError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
            if not (-180.0 <= longitude <= 180.0):
                raise ValidationError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
            if accuracy_meters is not None and accuracy_meters < 0:
                raise ValidationError("accuracy_meters cannot be negative.")

            loc = Location(
                latitude=latitude,
                longitude=longitude,
                accuracy_meters=accuracy_meters,
                address_raw=address_raw,
            )
            self.session.add(loc)
            await self.session.flush()

        # 5. Determine evidence type
        if evidence_type is None:
            if content_type.startswith("video/"):
                ev_type = EvidenceType.VIDEO
            else:
                ev_type = EvidenceType.IMAGE
        else:
            ev_type = evidence_type

        # 6. Pre-generate Evidence ID and safe storage key
        evidence_id = uuid.uuid4()
        storage_key = self.storage_service.generate_storage_key(
            incident_id=incident_id,
            evidence_id=evidence_id,
            filename=filename,
        )

        # 7. Upload to Supabase Storage
        storage_meta = await self.storage_service.upload_object(
            storage_key=storage_key,
            content=file_content,
            mime_type=content_type,
        )

        # 8. Persist to DB with compensation rollback
        evidence = Evidence(
            id=evidence_id,
            incident_id=incident_id,
            evidence_type=ev_type,
            status=EvidenceStatus.PENDING,
            description=description,
            occurred_at=occurred_at,
            location_id=loc.id if loc else None,
            storage_key=storage_meta.storage_key,
            mime_type=content_type,
            file_size_bytes=storage_meta.file_size_bytes,
        )

        try:
            await self.evidence_repo.create(evidence)
            incident.evidence_count += 1

            event = IncidentEvent(
                incident_id=incident_id,
                event_type=EventType.EVIDENCE_SUBMITTED,
                actor="user",
                summary=f"New {ev_type.value} evidence uploaded",
                payload={"evidence_id": str(evidence.id), "storage_key": storage_meta.storage_key},
            )
            await self.event_repo.create(event)
            await self.session.commit()
        except Exception as exc:
            # Compensation: delete uploaded object from storage
            logger.error(
                "evidence_db_persistence_failed_compensating_storage",
                incident_id=str(incident_id),
                evidence_id=str(evidence_id),
                storage_key=storage_key,
                error=str(exc),
            )
            try:
                await self.storage_service.delete_object(storage_key)
            except Exception as cleanup_exc:
                logger.warning(
                    "evidence_storage_cleanup_failed",
                    storage_key=storage_key,
                    cleanup_error=str(cleanup_exc),
                )
            if isinstance(exc, CivicTraceError):
                raise
            raise ServiceUnavailableError("Failed to persist evidence record.") from exc

        # Return refreshed evidence with loaded relationships
        return await self.evidence_repo.get_by_id(evidence_id) or evidence

    async def list_evidence(self, incident_id: uuid.UUID) -> Sequence[Evidence]:
        # Ensure incident exists
        await self.incident_service.get_incident(incident_id)
        return await self.evidence_repo.get_by_incident(incident_id)

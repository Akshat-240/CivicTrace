"""
Evidence business logic.
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventType, EvidenceStatus
from app.models.event import IncidentEvent
from app.models.evidence import Evidence
from app.models.location import Location
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.event_repo import EventRepository
from app.schemas.evidence import EvidenceSubmit
from app.services.incident_service import IncidentService


class EvidenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        self.event_repo = EventRepository(session)
        self.incident_service = IncidentService(session)

    async def add_evidence(
        self, incident_id: uuid.UUID, data: EvidenceSubmit
    ) -> Evidence:
        """
        Adds evidence to an existing incident.
        Sets status to PENDING (awaiting perception).
        """
        # Ensure incident exists
        incident = await self.incident_service.get_incident(incident_id)

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

        # Update incident evidence count (simplified for MVP)
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

    async def list_evidence(self, incident_id: uuid.UUID) -> Sequence[Evidence]:
        # Ensure incident exists
        await self.incident_service.get_incident(incident_id)
        return await self.evidence_repo.get_by_incident(incident_id)

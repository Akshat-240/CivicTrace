"""
Incident business logic.
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.enums import EventType, IncidentStatus
from app.models.event import IncidentEvent
from app.models.incident import Incident
from app.models.location import Location
from app.models.priority import Priority
from app.models.sla import SLA
from app.models.verification import VerificationRecord
from app.repositories.event_repo import EventRepository
from app.repositories.incident_repo import IncidentRepository
from app.schemas.incident import IncidentSubmit


class IncidentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)
        self.event_repo = EventRepository(session)

    async def create_incident(self, data: IncidentSubmit) -> Incident:
        """
        Creates a new draft incident.

        In a real flow, AI perception and GIS would follow asynchronously.
        For MVP API, we store it and mark as DRAFT.
        """
        # Create location if provided
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

        incident = Incident(
            reference_number=f"INC-{uuid.uuid4().hex[:8].upper()}",
            status=IncidentStatus.DRAFT,
            issue_type=data.issue_type,
            title=data.title,
            description=data.description,
            location_id=loc.id if loc else None,
            evidence_count=0,
        )
        await self.incident_repo.create(incident)

        # Create timeline event
        event = IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.INCIDENT_CREATED,
            actor="user",
            summary="Incident submitted via API",
        )
        await self.event_repo.create(event)

        return await self.get_incident(incident.id)

    async def get_incident(self, incident_id: uuid.UUID) -> Incident:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found.")
        return incident

    async def assign_jurisdiction(self, incident_id: uuid.UUID) -> Incident:
        """
        Runs the GIS detection for the incident's location and assigns the Jurisdiction and Authority.
        """
        from app.services.gis_service import GISService
        from app.schemas.gis import GISStatus

        incident = await self.get_incident(incident_id)
        
        if not incident.location:
            # Cannot resolve without a location
            event = IncidentEvent(
                incident_id=incident.id,
                event_type=EventType.SYSTEM_NOTE,
                actor="system",
                summary="GIS resolution failed: No location attached to incident.",
            )
            await self.event_repo.create(event)
            await self.session.commit()
            return await self.get_incident(incident.id)

        gis_service = GISService(self.session)
        result = await gis_service.resolve_jurisdiction(
            latitude=incident.location.latitude,
            longitude=incident.location.longitude,
        )

        if result.status == GISStatus.JURISDICTION_FOUND:
            incident.jurisdiction_id = result.jurisdiction_id
            incident.authority_id = result.authority_id
            
            # Record events
            await self.event_repo.create(IncidentEvent(
                incident_id=incident.id,
                event_type=EventType.JURISDICTION_ASSIGNED,
                actor="system",
                summary=result.explanation,
            ))
            await self.event_repo.create(IncidentEvent(
                incident_id=incident.id,
                event_type=EventType.AUTHORITY_ASSIGNED,
                actor="system",
                summary=f"Authority assigned based on GIS containment.",
            ))
        else:
            # Conflict or invalid
            await self.event_repo.create(IncidentEvent(
                incident_id=incident.id,
                event_type=EventType.SYSTEM_NOTE,
                actor="system",
                summary=f"GIS resolution issue ({result.status.value}): {result.explanation}",
            ))

        await self.session.commit()
        return await self.get_incident(incident.id)

    async def list_incidents(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Incident], int]:
        return await self.incident_repo.list_incidents(skip, limit)

    async def get_incident_timeline(self, incident_id: uuid.UUID) -> Sequence[IncidentEvent]:
        # Ensure incident exists
        await self.get_incident(incident_id)
        return await self.event_repo.get_by_incident(incident_id)

    async def get_incident_accountability(self, incident_id: uuid.UUID) -> SLA:
        incident = await self.get_incident(incident_id)
        if not incident.sla:
            raise NotFoundError(f"SLA accountability data not found for Incident {incident_id}.")
        return incident.sla

    async def get_incident_verification(self, incident_id: uuid.UUID) -> VerificationRecord:
        incident = await self.get_incident(incident_id)
        if not incident.verification:
            raise NotFoundError(f"Verification data not found for Incident {incident_id}.")
        return incident.verification

"""
Incident business logic.
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.enums import EventType, IncidentStatus
from app.models.event import IncidentEvent
from app.models.incident import Incident
from app.models.location import Location
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

    async def create_incident(self, data: IncidentSubmit, citizen_id: Optional[uuid.UUID] = None) -> Incident:
        """
        Create a new incident with its initial location.
        Always starts in DRAFT state.
        """
        # Validate coordinate constraints if location is provided
        loc = None
        if data.location:
            if not (-90.0 <= data.location.latitude <= 90.0):
                raise ValidationError("Latitude must be between -90 and 90.")
            if not (-180.0 <= data.location.longitude <= 180.0):
                raise ValidationError("Longitude must be between -180 and 180.")

            loc = Location(
                latitude=data.location.latitude,
                longitude=data.location.longitude,
                accuracy_meters=data.location.accuracy_meters,
                address_raw=data.location.address_raw,
            )
            self.session.add(loc)
            await self.session.flush()

        metadata = dict(data.fusion_metadata or {})
        if citizen_id:
            metadata["citizen_id"] = str(citizen_id)

        incident = Incident(
            reference_number=f"INC-{uuid.uuid4().hex[:8].upper()}",
            status=IncidentStatus.DRAFT,
            issue_type=data.issue_type,
            title=data.title,
            description=data.description,
            location_id=loc.id if loc else None,
            fusion_metadata=metadata,
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
        
        await self.session.flush()
        
        # Run orchestration workflow
        await self.process_incident_workflow(incident.id)

        return await self.get_incident(incident.id)

    async def process_incident_workflow(self, incident_id: uuid.UUID) -> None:
        """
        Orchestrates the lifecycle for a new incident:
        1. GIS Jurisdiction Resolution
        2. SLA Clock Start
        """
        from app.services.sla_service import AccountabilityService

        # 1. GIS assignment
        incident = await self.assign_jurisdiction(incident_id)

        # refresh incident to get latest state
        incident = await self.get_incident(incident.id)

        # 2. SLA start (only if authority was assigned)
        if incident.authority_id:
            sla_service = AccountabilityService(self.session)
            await sla_service.start_sla(incident.id)

    async def get_incident(self, incident_id: uuid.UUID | str) -> Incident:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found.")
        await self.session.refresh(
            incident,
            ["location", "jurisdiction", "authority", "sla", "verification"],
        )
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
            await self.session.flush()
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

        await self.session.flush()
        return await self.get_incident(incident.id)

    async def list_incidents(
        self, skip: int = 0, limit: int = 20, citizen_id: Optional[str] = None, authority_id: Optional[str] = None
    ) -> tuple[Sequence[Incident], int]:
        return await self.incident_repo.list_incidents(skip, limit, citizen_id=citizen_id, authority_id=authority_id)

    async def get_incident_timeline(self, incident_id: uuid.UUID | str) -> Sequence[IncidentEvent]:
        # Ensure incident exists
        incident = await self.get_incident(incident_id)
        return await self.event_repo.get_by_incident(incident.id)

    async def get_incident_accountability(self, incident_id: uuid.UUID | str) -> SLA:
        incident = await self.get_incident(incident_id)
        if not incident.sla:
            raise NotFoundError(f"SLA accountability data not found for Incident {incident_id}.")
        return incident.sla

    async def get_incident_verification(self, incident_id: uuid.UUID | str) -> VerificationRecord:
        incident = await self.get_incident(incident_id)
        if not incident.verification:
            raise NotFoundError(f"Verification data not found for Incident {incident_id}.")
        return incident.verification


    async def close_incident(self, incident_id: uuid.UUID | str) -> Incident:
        """
        Closes a RESOLVED incident.

        Guard: only RESOLVED incidents can be closed.
        ACTIVE, UNDER_REVIEW, DRAFT, INVALID -> ConflictError.
        CLOSED -> returns as-is (idempotent).

        Uses flush() only -- get_db() commits at request end.
        """
        from app.core.errors import ConflictError

        incident = await self.get_incident(incident_id)

        if incident.status == IncidentStatus.CLOSED:
            return incident  # Already closed -- idempotent.

        if incident.status != IncidentStatus.RESOLVED:
            raise ConflictError(
                f"Only RESOLVED incidents can be closed. "
                f"Current status: {incident.status.value}. "
                f"Ensure human verification has approved a FULLY_RESOLVED decision first."
            )

        incident.status = IncidentStatus.CLOSED

        await self.event_repo.create(IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.INCIDENT_STATUS_CHANGED,
            actor="authority",
            summary="Incident closed after verified resolution.",
            payload={"previous_status": "resolved", "new_status": "closed"},
        ))
        await self.session.flush()

        return await self.get_incident(incident.id)


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
        Creates or fuses a new incident report submission.
        Invokes FusionService to determine if this report matches an existing incident.
        If fused, evidence is attached to the canonical incident.
        If new, runs GIS jurisdiction assignment and starts the SLA clock.
        """
        from datetime import datetime, timezone
        from app.models.enums import EvidenceStatus, EvidenceType
        from app.models.evidence import Evidence
        from app.services.fusion_service import FusionService

        # 1. Create location if provided
        loc = None
        if data.location:
            loc = Location(
                latitude=data.location.latitude,
                longitude=data.location.longitude,
                accuracy_meters=data.location.accuracy_meters,
                address_raw=data.location.address_raw,
                geom=f"SRID=4326;POINT({data.location.longitude} {data.location.latitude})",
            )
            self.session.add(loc)
            await self.session.flush()

        # 2. Create atomic Evidence item for this citizen report submission
        cat_str = data.issue_type.value if hasattr(data.issue_type, "value") else (str(data.issue_type) if data.issue_type else None)
        evidence = Evidence(
            evidence_type=EvidenceType.TEXT,
            status=EvidenceStatus.PROCESSED,
            description=data.description or data.title,
            ai_category=cat_str,
            location_id=loc.id if loc else None,
            occurred_at=datetime.now(timezone.utc),
        )
        self.session.add(evidence)
        await self.session.flush()

        # 3. Invoke FusionService
        fusion_service = FusionService(self.session)
        incident = await fusion_service.fuse_evidence(
            evidence_id=evidence.id,
            title=data.title,
            description=data.description,
        )

        # 4. If a new incident was created, run orchestration workflow (GIS + SLA)
        is_new_incident = (incident.primary_evidence_id == evidence.id)
        if is_new_incident:
            await self.process_incident_workflow(incident.id)

        return await self.get_incident(incident.id)

    async def process_incident_workflow(self, incident_id: uuid.UUID) -> None:
        """
        Orchestrates the lifecycle for a new incident:
        1. GIS Jurisdiction Resolution
        2. SLA Clock Start (based on Authority + Issue Type)
        """
        from app.services.sla_service import AccountabilityService

        # 1. GIS assignment
        incident = await self.assign_jurisdiction(incident_id)

        # 2. SLA start (only if authority was assigned)
        if incident.authority_id:
            sla_service = AccountabilityService(self.session)
            await sla_service.start_sla(incident.id)

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


    async def close_incident(self, incident_id: uuid.UUID) -> Incident:
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

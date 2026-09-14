"""
Data access for Incidents and related aggregates.
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident import Incident
from app.models.location import Location


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def get_by_id(self, incident_id: uuid.UUID | str) -> Optional[Incident]:
        if isinstance(incident_id, uuid.UUID):
            condition = (Incident.id == incident_id)
        else:
            try:
                parsed_uuid = uuid.UUID(str(incident_id))
                condition = (Incident.id == parsed_uuid) | (Incident.reference_number == str(incident_id))
            except ValueError:
                condition = (Incident.reference_number == str(incident_id))

        stmt = (
            select(Incident)
            .where(condition)
            .options(
                selectinload(Incident.location),
                selectinload(Incident.jurisdiction),
                selectinload(Incident.authority),
                selectinload(Incident.priority),
                selectinload(Incident.sla),
                selectinload(Incident.verification),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_incidents(
        self, skip: int = 0, limit: int = 20, citizen_id: Optional[str] = None, authority_id: Optional[str] = None
    ) -> tuple[Sequence[Incident], int]:
        """Return a paginated list of incidents and the total count."""
        count_stmt = select(func.count()).select_from(Incident)
        data_stmt = (
            select(Incident)
            .options(
                selectinload(Incident.location),
                selectinload(Incident.jurisdiction),
                selectinload(Incident.authority),
                selectinload(Incident.priority),
                selectinload(Incident.sla),
                selectinload(Incident.verification),
            )
            .order_by(Incident.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        filter_clauses = []
        if citizen_id:
            if citizen_id == "citizen_default":
                filter_clauses.append(
                    Incident.fusion_metadata.contains({"citizen_id": citizen_id})
                    | (Incident.fusion_metadata.is_(None))
                )
            else:
                filter_clauses.append(Incident.fusion_metadata.contains({"citizen_id": citizen_id}))
        
        if authority_id:
            try:
                auth_uuid = uuid.UUID(str(authority_id))
                filter_clauses.append(Incident.authority_id == auth_uuid)
            except ValueError:
                pass

        if filter_clauses:
            for clause in filter_clauses:
                count_stmt = count_stmt.where(clause)
                data_stmt = data_stmt.where(clause)

        total = await self.session.scalar(count_stmt) or 0
        result = await self.session.execute(data_stmt)
        incidents = result.scalars().all()
        
        return incidents, total

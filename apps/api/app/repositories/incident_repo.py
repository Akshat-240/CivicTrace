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

    async def get_by_id(self, incident_id: uuid.UUID) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(
                selectinload(Incident.location),
                selectinload(Incident.jurisdiction),
                selectinload(Incident.authority),
                selectinload(Incident.sla),
                selectinload(Incident.verification),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_incidents(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Incident], int]:
        """Return a paginated list of incidents and the total count."""
        # Total count
        count_stmt = select(func.count()).select_from(Incident)
        total = await self.session.scalar(count_stmt) or 0

        # Data
        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.location),
                selectinload(Incident.authority),
                selectinload(Incident.sla),
                selectinload(Incident.verification),
            )
            .order_by(Incident.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        incidents = result.scalars().all()
        
        return incidents, total

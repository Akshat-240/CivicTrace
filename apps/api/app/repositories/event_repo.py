"""
Data access for Incident Events (Timeline).
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import IncidentEvent


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: IncidentEvent) -> IncidentEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_incident(self, incident_id: uuid.UUID) -> Sequence[IncidentEvent]:
        stmt = (
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

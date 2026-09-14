"""
Data access for Evidence.
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.evidence import Evidence


class EvidenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, evidence: Evidence) -> Evidence:
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def get_by_id(self, evidence_id: uuid.UUID) -> Evidence | None:
        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_incident(self, incident_id: uuid.UUID) -> Sequence[Evidence]:
        stmt = (
            select(Evidence)
            .where(Evidence.incident_id == incident_id)
            .options(selectinload(Evidence.location))
            .order_by(Evidence.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

"""
GIS spatial analysis service.
"""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.jurisdiction import Jurisdiction
from app.schemas.gis import GISStatus, JurisdictionResult


class GISService:
    """
    Handles all PostGIS spatial lookups and geographic determinations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve_jurisdiction(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> JurisdictionResult:
        """
        Determine the responsible jurisdiction for the given coordinates.
        Uses PostGIS ST_Contains for point-in-polygon assignment.
        """
        # 1. Validate coordinates
        if latitude is None or longitude is None:
            return JurisdictionResult(
                status=GISStatus.INVALID_LOCATION,
                explanation="Missing latitude or longitude."
            )

        if not (-90.0 <= latitude <= 90.0):
            return JurisdictionResult(
                status=GISStatus.INVALID_LOCATION,
                explanation=f"Invalid latitude: {latitude}. Must be between -90 and 90."
            )

        if not (-180.0 <= longitude <= 180.0):
            return JurisdictionResult(
                status=GISStatus.INVALID_LOCATION,
                explanation=f"Invalid longitude: {longitude}. Must be between -180 and 180."
            )

        # 2. Perform Spatial Lookup
        # We construct a PostGIS point: ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        # Note the ordering: longitude (X) comes first, then latitude (Y).
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        stmt = (
            select(Jurisdiction)
            .options(selectinload(Jurisdiction.authority))
            .where(func.ST_Contains(Jurisdiction.boundary, point))
        )
        
        try:
            result = await self.session.execute(stmt)
            matches = result.scalars().all()
        except Exception as e:
            # Handle database/PostGIS failures gracefully
            return JurisdictionResult(
                status=GISStatus.JURISDICTION_CONFLICT,
                explanation=f"GIS database query failed: {str(e)}"
            )

        # 3. Handle Conflicts and No-Matches
        if len(matches) == 0:
            return JurisdictionResult(
                status=GISStatus.NO_JURISDICTION,
                explanation="Coordinates do not fall within any known civic boundary."
            )
            
        if len(matches) > 1:
            # Multiple overlapping boundaries found
            names = ", ".join([m.name for m in matches])
            return JurisdictionResult(
                status=GISStatus.JURISDICTION_CONFLICT,
                explanation=f"Coordinates fall within multiple overlapping boundaries: {names}. Manual review required."
            )

        # 4. Success Match
        match = matches[0]
        if not match.authority:
            return JurisdictionResult(
                status=GISStatus.JURISDICTION_CONFLICT,
                explanation=f"Jurisdiction '{match.name}' has no mapped authority."
            )

        return JurisdictionResult(
            status=GISStatus.JURISDICTION_FOUND,
            jurisdiction_id=match.id,
            authority_id=match.authority_id,
            explanation=f"Location falls within '{match.name}' boundary, which is mapped to authority '{match.authority.name}'."
        )

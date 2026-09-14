"""
GIS endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import DbSession
from app.schemas.gis import JurisdictionResult
from app.services.gis_service import GISService

router = APIRouter(prefix="/gis", tags=["gis"])


@router.get(
    "/jurisdiction",
    response_model=JurisdictionResult,
    summary="Resolve jurisdiction for coordinates",
)
async def resolve_jurisdiction(
    db: DbSession,
    latitude: float = Query(..., description="Latitude (-90 to 90)"),
    longitude: float = Query(..., description="Longitude (-180 to 180)"),
) -> Any:
    service = GISService(db)
    return await service.resolve_jurisdiction(latitude, longitude)

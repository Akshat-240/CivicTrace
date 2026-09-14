"""
GIS and spatial schemas.
"""

import enum
import uuid
from typing import Optional

from app.schemas.base import CivicBaseModel


class GISStatus(str, enum.Enum):
    JURISDICTION_FOUND = "JURISDICTION_FOUND"
    NO_JURISDICTION = "NO_JURISDICTION"
    JURISDICTION_CONFLICT = "JURISDICTION_CONFLICT"
    INVALID_LOCATION = "INVALID_LOCATION"


class JurisdictionResult(CivicBaseModel):
    """
    Structured result from the GIS spatial containment lookup.
    """
    status: GISStatus
    jurisdiction_id: Optional[uuid.UUID] = None
    authority_id: Optional[uuid.UUID] = None
    explanation: str

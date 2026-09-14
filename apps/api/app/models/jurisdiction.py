"""
Jurisdiction ORM model.

A Jurisdiction represents a geographic administrative boundary owned
by a civic Authority. Point-in-polygon GIS queries against the `boundary`
column determine which Jurisdiction (and therefore which Authority) is
responsible for an incident at a given location.

Design notes:
- One Authority can own multiple Jurisdictions (e.g. state + local zones).
- A Jurisdiction belongs to exactly one Authority.
- The `boundary` column is a PostGIS MULTIPOLYGON (to allow non-contiguous
  regions such as an island + mainland pair).
- The GIS service writes to this table; the API reads from it.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.authority import Authority
    from app.models.incident import Incident
    from app.models.location import Location


class Jurisdiction(Base):
    """
    Administrative boundary that determines authority responsibility.

    The GIS service performs ST_Contains(boundary, location.geom) to
    assign a Jurisdiction to every incoming incident.
    """

    __tablename__ = "jurisdictions"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Owning authority (FK)
    # ------------------------------------------------------------------
    authority_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("authorities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Geographic boundary
    # ------------------------------------------------------------------
    # PostGIS MULTIPOLYGON, WGS-84 (SRID 4326)
    # spatial_index=True creates a GIST index automatically via GeoAlchemy2.
    boundary: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,   # Null until GIS data is loaded via seed/data pipeline
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    authority: Mapped["Authority"] = relationship(
        "Authority", back_populates="jurisdictions"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="jurisdiction"
    )
    locations: Mapped[list["Location"]] = relationship(
        "Location",
        primaryjoin="foreign(Location.id) == Jurisdiction.id",  # GIS-resolved
        viewonly=True,
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_jurisdictions_authority_id", "authority_id"),
    )

    def __repr__(self) -> str:
        return f"<Jurisdiction id={self.id} code={self.code!r}>"

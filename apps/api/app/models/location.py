"""
Location ORM model.

A Location is a first-class entity — not a simple pair of columns —
because it:
  1. Carries a PostGIS geometry column for spatial queries.
  2. Can be referenced by both Incidents and Evidence independently.
  3. Stores human-readable address fields alongside the geometry.

PostGIS geometry column uses WGS-84 (SRID 4326) — the same coordinate
system used by GPS, Google Maps and GeoJSON.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geometry
from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.evidence import Evidence
    from app.models.jurisdiction import Jurisdiction


class Location(Base):
    """
    Geographic location with PostGIS geometry support.

    The `geom` column stores a PostGIS POINT geometry (SRID 4326).
    latitude / longitude are stored redundantly for fast non-spatial
    lookups (e.g. API response serialisation without ST_X/ST_Y calls).
    """

    __tablename__ = "locations"

    # ------------------------------------------------------------------
    # Coordinates (human-readable redundant copy)
    # ------------------------------------------------------------------
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # PostGIS point geometry — WGS-84 / EPSG:4326
    geom: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,   # populated by a trigger / service after row insert
    )

    # ------------------------------------------------------------------
    # Human-readable address fields (AI-extracted or reverse-geocoded)
    # ------------------------------------------------------------------
    address_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    street: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    suburb: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Accuracy of the reported location in metres (AI / GPS estimate)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="location", foreign_keys="Incident.location_id"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="location"
    )
    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship(
        "Jurisdiction", back_populates="locations", foreign_keys="Jurisdiction.id",
        primaryjoin="Location.id == foreign(Jurisdiction.id)",  # resolved via GIS join
        viewonly=True,
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Composite index for bounding-box queries without PostGIS
        Index("ix_locations_lat_lng", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Location id={self.id} lat={self.latitude} lng={self.longitude}>"

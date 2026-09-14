"""
Asset ORM model.

An Asset is an optional link between an Incident and an infrastructure
record (a road segment, streetlight, drain, etc.). An Incident may have
zero or more Assets.

Assets are informational — they allow an authority to track which specific
piece of infrastructure is damaged without requiring a full asset registry
to exist upfront. The `external_asset_id` can reference an external CMMS
or GIS asset database when one is available.

No business logic lives here.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AssetType

if TYPE_CHECKING:
    from app.models.incident import Incident


class Asset(Base):
    """
    Infrastructure asset associated with an incident.

    Examples:
    - A specific road segment (road_id from council GIS)
    - A streetlight pole number
    - A drain catch pit reference
    """

    __tablename__ = "assets"

    # ------------------------------------------------------------------
    # Incident link
    # ------------------------------------------------------------------
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Asset identity
    # ------------------------------------------------------------------
    asset_type: Mapped[AssetType] = mapped_column(
        String(50), nullable=False, index=True
    )

    # Human-readable name (e.g. "Main St between Oak Ave and Pine Rd")
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Reference ID in an external asset registry (e.g. council GIS ID)
    external_asset_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extra structured metadata (e.g. {"road_class": "arterial", "speed_limit": 60})
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped["Incident"] = relationship("Incident", back_populates="assets")

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_assets_incident_type", "incident_id", "asset_type"),
    )

    def __repr__(self) -> str:
        return f"<Asset id={self.id} type={self.asset_type!r} incident={self.incident_id}>"

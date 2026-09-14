"""
Incident ORM model.

The Incident is the canonical domain entity in CivicTrace. It represents a
fused, de-duplicated civic issue that has been:
  1. Reported via one or more Evidence items.
  2. Classified by AI perception.
  3. Located in a Jurisdiction.
  4. Assigned to an Authority.
  5. Prioritised and tracked through to resolution.

Design notes:
- An Incident is created by the fusion service when evidence cannot be
  merged into an existing open incident.
- An Incident holds foreign keys to Location, Jurisdiction, Authority.
  These are nullable until each pipeline stage completes.
- Processing metadata (ai_category, ai_confidence, fusion_group_id) captures
  what the AI/fusion services determined WITHOUT encoding business logic.
- All state transitions are recorded in the IncidentEvent timeline.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IncidentStatus, IssueType

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.location import Location
    from app.models.jurisdiction import Jurisdiction
    from app.models.authority import Authority
    from app.models.asset import Asset
    from app.models.sla import SLA
    from app.models.verification import VerificationRecord
    from app.models.event import IncidentEvent


class Incident(Base):
    """
    Fused civic incident — the core CivicTrace domain entity.

    Nullable FKs are populated as each pipeline stage completes:
      location_id      → set when first evidence is processed
      jurisdiction_id  → set by GIS service
      authority_id     → set by authority assignment service
    """

    __tablename__ = "incidents"

    # ------------------------------------------------------------------
    # Identity & classification
    # ------------------------------------------------------------------
    # Human-readable display identifier (e.g. "INC-2026-001234")
    reference_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )

    status: Mapped[IncidentStatus] = mapped_column(
        String(30), nullable=False, default=IncidentStatus.DRAFT, index=True
    )
    issue_type: Mapped[Optional[IssueType]] = mapped_column(
        String(50), nullable=True, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Pipeline foreign keys (populated progressively)
    # ------------------------------------------------------------------
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    jurisdiction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    authority_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # AI perception metadata
    # ------------------------------------------------------------------
    # Category returned by AI (may differ from final issue_type if overridden)
    ai_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    # Structured output from AI perception stored for auditability
    ai_perception_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    # True if AI flagged ambiguity — SLA clock may be paused until reviewed
    ai_ambiguity_flag: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )

    # ------------------------------------------------------------------
    # Fusion metadata
    # ------------------------------------------------------------------
    # UUID of the "primary" evidence that triggered incident creation
    primary_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    evidence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    # Fusion scoring metadata (stored for explainability, not used in queries)
    fusion_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    location: Mapped[Optional["Location"]] = relationship(
        "Location", back_populates="incidents", foreign_keys=[location_id]
    )
    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship(
        "Jurisdiction", back_populates="incidents"
    )
    authority: Mapped[Optional["Authority"]] = relationship(
        "Authority", back_populates="incidents"
    )

    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="incident", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", back_populates="incident", cascade="all, delete-orphan"
    )
    sla: Mapped[Optional["SLA"]] = relationship(
        "SLA",
        back_populates="incident",
        uselist=False,
        cascade="all, delete-orphan",
    )
    verification: Mapped[Optional["VerificationRecord"]] = relationship(
        "VerificationRecord",
        back_populates="incident",
        uselist=False,
        cascade="all, delete-orphan",
    )
    events: Mapped[list["IncidentEvent"]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        order_by="IncidentEvent.created_at",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Indexes & constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_incidents_status_created_at", "status", "created_at"),
        Index("ix_incidents_issue_type_status", "issue_type", "status"),
        Index("ix_incidents_jurisdiction_status", "jurisdiction_id", "status"),
        Index("ix_incidents_authority_status", "authority_id", "status"),
        CheckConstraint(
            "(jurisdiction_id IS NULL AND authority_id IS NULL) OR (jurisdiction_id IS NOT NULL)",
            name="ck_incidents_jurisdiction_authority_invariant",
        ),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)",
            name="ck_incidents_ai_confidence_range",
        ),
        CheckConstraint(
            "evidence_count >= 0",
            name="ck_incidents_evidence_count_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Incident id={self.id} ref={self.reference_number!r} "
            f"status={self.status!r}>"
        )

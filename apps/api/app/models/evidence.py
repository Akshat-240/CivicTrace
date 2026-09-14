"""
Evidence ORM model.

Evidence is the atomic unit of user input into CivicTrace. Each submission
(image, video, text) becomes one Evidence row. Evidence rows are linked to
an Incident after the fusion service runs.

Design notes:
- Evidence is never modified after AI perception completes (append-only spirit).
- AI-extracted fields (ai_*) are populated by the perception service after
  the row is created.
- An Evidence item carries its own Location so that fusion can compare
  whether two pieces of evidence are co-located.
- `storage_key` is the cloud object path (e.g. S3/GCS key). The API
  constructs the full URL at response time — never stored in the DB.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EvidenceStatus, EvidenceType, EvidencePhase

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.location import Location


class Evidence(Base):
    """
    A single piece of raw evidence submitted by a reporter.

    After AI perception, `ai_*` columns are populated and `status` moves
    to PROCESSED. The fusion service then links this evidence to an Incident.
    """

    __tablename__ = "evidence"

    # ------------------------------------------------------------------
    # Submission metadata
    # ------------------------------------------------------------------
    evidence_type: Mapped[EvidenceType] = mapped_column(
        String(20), nullable=False, index=True
    )
    # When in the lifecycle this evidence was gathered
    evidence_phase: Mapped[Optional[EvidencePhase]] = mapped_column(
        String(20), nullable=True, default=EvidencePhase.BEFORE
    )
    status: Mapped[EvidenceStatus] = mapped_column(
        String(20), nullable=False, default=EvidenceStatus.PENDING, index=True
    )

    # When the event being reported actually occurred (as reported by submitter)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    # Object storage key (path within bucket, not full URL)
    storage_key: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # MIME type (e.g. "image/jpeg", "video/mp4")
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # File size in bytes
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    # Free-text description provided by the reporter
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Incident link (set by fusion service)
    # ------------------------------------------------------------------
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Location (submitted with evidence)
    # ------------------------------------------------------------------
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # AI perception output
    # ------------------------------------------------------------------
    ai_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_severity_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_safety_risk: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # Full structured perception payload (stored for auditability)
    ai_perception_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # True if AI flagged this evidence as ambiguous
    ai_ambiguity_flag: Mapped[bool] = mapped_column(nullable=False, default=False)
    # Human-readable reason for ambiguity (if flagged)
    ai_ambiguity_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Verification: was this used as before/after evidence?
    # ------------------------------------------------------------------
    # True if this evidence was submitted as post-resolution proof
    is_verification_evidence: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident", back_populates="evidence_items"
    )
    location: Mapped[Optional["Location"]] = relationship(
        "Location", back_populates="evidence_items"
    )

    # ------------------------------------------------------------------
    # Indexes & constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_evidence_incident_type", "incident_id", "evidence_type"),
        Index("ix_evidence_status_created_at", "status", "created_at"),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)",
            name="ck_evidence_ai_confidence_range",
        ),
        CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes > 0",
            name="ck_evidence_file_size_positive",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence id={self.id} type={self.evidence_type!r} "
            f"status={self.status!r}>"
        )


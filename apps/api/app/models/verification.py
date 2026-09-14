"""
Verification ORM model.

A VerificationRecord is a 1-to-1 companion to an Incident. It is created
when resolution verification is submitted (either by an authority, inspector,
or a second round of public evidence).

Verification stores:
- References to "before" evidence (the original report)
- References to "after" evidence (the resolution proof)
- The verification result (one of the four canonical states)
- A confidence score (AI-assisted or human-set)
- A human-readable explanation

Design notes:
- before_evidence_id and after_evidence_id are soft references to Evidence
  rows (nullable FKs). They are informational — no cascade delete.
- The verification result is SET ONLY by the verification service, never
  by route handlers directly.
- A single incident may have multiple verification attempts (if partial
  resolution is submitted first). Only the LATEST record is used.
  The full history is in the IncidentEvent timeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import VerificationResult

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.evidence import Evidence


class VerificationRecord(Base):
    """
    Resolution verification for an Incident.

    Stores before/after evidence references and the outcome of the
    verification process.
    """

    __tablename__ = "verification_records"

    # ------------------------------------------------------------------
    # Incident link (1-to-1 current record)
    # ------------------------------------------------------------------
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # Only one current verification per incident
        index=True,
    )

    # ------------------------------------------------------------------
    # Evidence references
    # ------------------------------------------------------------------
    # Evidence that captured the issue BEFORE resolution
    before_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Evidence that proves resolution AFTER fix
    after_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Verification outcome
    # ------------------------------------------------------------------
    result: Mapped[Optional[VerificationResult]] = mapped_column(
        String(30), nullable=True, index=True
    )

    # AI-assisted confidence in the result (0.0 – 1.0)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Human-readable explanation of why this result was assigned
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Who/what set the result: "ai", "inspector", "public", "authority"
    verified_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped["Incident"] = relationship(
        "Incident", back_populates="verification"
    )
    before_evidence: Mapped[Optional["Evidence"]] = relationship(
        "Evidence",
        foreign_keys=[before_evidence_id],
    )
    after_evidence: Mapped[Optional["Evidence"]] = relationship(
        "Evidence",
        foreign_keys=[after_evidence_id],
    )

    # ------------------------------------------------------------------
    # Indexes & constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_verification_confidence_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<VerificationRecord id={self.id} incident={self.incident_id} "
            f"result={self.result!r}>"
        )

"""
Priority ORM model.

A Priority record is a 1-to-1 companion to an Incident. It stores the
output of the Priority Engine — a purely deterministic calculation based
on three inputs:
  - Severity   (physical damage scale)
  - Safety     (immediate risk to persons)
  - Persistence (how long the issue has existed / evidence count)

The `explanation` field stores a human-readable justification of the
computed level (e.g. "HIGH — safety risk detected, critical severity").

No scoring logic lives here. This is a pure data record.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PriorityLevel, SeverityLevel

if TYPE_CHECKING:
    from app.models.incident import Incident


class Priority(Base):
    """
    Priority assessment for an Incident.

    score_* columns store normalised 0–1 inputs used by the engine.
    final_priority stores the discrete output used for SLA and dashboards.
    """

    __tablename__ = "priorities"

    # ------------------------------------------------------------------
    # Incident link (1-to-1)
    # ------------------------------------------------------------------
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # enforces 1-to-1
        index=True,
    )

    # ------------------------------------------------------------------
    # Input factors
    # ------------------------------------------------------------------
    severity: Mapped[Optional[SeverityLevel]] = mapped_column(
        String(20), nullable=True
    )
    safety_risk: Mapped[bool] = mapped_column(nullable=False, default=False)
    # Persistence score: 0.0–1.0 (computed from age + evidence count)
    persistence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    final_priority: Mapped[Optional[PriorityLevel]] = mapped_column(
        String(20), nullable=True, index=True
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped["Incident"] = relationship(
        "Incident", back_populates="priority"
    )

    # ------------------------------------------------------------------
    # Indexes & constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "persistence_score IS NULL OR "
            "(persistence_score >= 0.0 AND persistence_score <= 1.0)",
            name="ck_priorities_persistence_score_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Priority id={self.id} incident={self.incident_id} "
            f"final={self.final_priority!r}>"
        )

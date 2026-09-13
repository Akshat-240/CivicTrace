"""
SLA (Service Level Agreement) ORM model.

A SLA record tracks the accountability lifecycle for one Incident.
It is a 1-to-1 companion to an Incident created when the Incident
is confirmed and assigned to an Authority.

State machine:
  PENDING → DUE → OVERDUE → ESCALATION_ELIGIBLE
  Any state → RESOLVED (terminal, set when verification confirms resolution)

The accountability engine is responsible for advancing these states.
This model simply stores the current state and timestamps.

Design notes:
- `started_at` is when the SLA clock started (normally when the incident
  transitions from DRAFT → ACTIVE, or when ambiguity is cleared).
- `due_at` is computed from Authority.sla_hours_<priority> + started_at.
- `escalated_at` records when the incident became escalation-eligible.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountabilityState

if TYPE_CHECKING:
    from app.models.incident import Incident


class SLA(Base):
    """
    SLA and accountability tracking for a confirmed Incident.

    The accountability engine reads this table and the current time to
    determine whether an incident needs a state transition.
    """

    __tablename__ = "slas"

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
    # State
    # ------------------------------------------------------------------
    state: Mapped[AccountabilityState] = mapped_column(
        Enum(AccountabilityState, native_enum=False, length=30, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountabilityState.PENDING,
        index=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # When state first became OVERDUE
    overdue_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # When state first became ESCALATION_ELIGIBLE
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Escalation
    # ------------------------------------------------------------------
    is_escalation_eligible: Mapped[bool] = mapped_column(
        nullable=False, default=False, index=True
    )
    # Free-text note set by the accountability engine when escalating
    escalation_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped["Incident"] = relationship("Incident", back_populates="sla")

    # ------------------------------------------------------------------
    # Indexes & constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        # Used by the accountability engine to find overdue incidents efficiently
        Index("ix_slas_state_due_at", "state", "due_at"),
        CheckConstraint(
            "due_at IS NULL OR started_at IS NULL OR due_at > started_at",
            name="ck_slas_due_after_start",
        ),
        CheckConstraint(
            "resolved_at IS NULL OR started_at IS NULL OR resolved_at >= started_at",
            name="ck_slas_resolved_after_start",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SLA id={self.id} incident={self.incident_id} "
            f"state={self.state!r} due={self.due_at}>"
        )

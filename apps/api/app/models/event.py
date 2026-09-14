"""
IncidentEvent ORM model — append-only incident timeline.

Every meaningful state change, evidence submission, priority computation,
SLA transition, and note is recorded here. The event log is the single
source of truth for the incident history displayed on the dashboard.

Design principles:
- APPEND ONLY. Events are never updated or deleted.
- No cascade delete on incident_id (we lose audit history if we did).
  Instead use ON DELETE RESTRICT so incidents can only be deleted after
  their events are archived.
- `actor` is a freeform string identifying who/what triggered the event
  (e.g. "system", "ai_perception", "authority:abc123", "user:xyz789").
- `payload` is a JSONB bag for event-specific structured data. The schema
  for each event type is documented in docs/api-contract.md, not enforced
  at the DB level (keep the event table flexible).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EventType

if TYPE_CHECKING:
    from app.models.incident import Incident


class IncidentEvent(Base):
    """
    A single entry in the incident timeline.

    created_at (from Base) is the canonical event timestamp.
    The table is ordered by created_at in the Incident relationship.
    """

    __tablename__ = "incident_events"

    # ------------------------------------------------------------------
    # Incident link — RESTRICT prevents orphan events
    # ------------------------------------------------------------------
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Event classification
    # ------------------------------------------------------------------
    event_type: Mapped[EventType] = mapped_column(
        String(60), nullable=False, index=True
    )

    # ------------------------------------------------------------------
    # Authorship
    # ------------------------------------------------------------------
    # Who or what triggered this event
    # Examples: "system", "ai_perception", "user:uuid", "authority:uuid"
    actor: Mapped[str] = mapped_column(String(200), nullable=False, default="system")

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    # Short summary shown on the timeline UI
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Extended human-readable detail (shown in expanded event view)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Structured event-specific data (schema varies by event_type)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    incident: Mapped["Incident"] = relationship(
        "Incident", back_populates="events"
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Timeline query: all events for an incident in chronological order
        Index("ix_incident_events_incident_created", "incident_id", "created_at"),
        # Filter by event type across all incidents (e.g. all escalations)
        Index("ix_incident_events_type_created", "event_type", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<IncidentEvent id={self.id} type={self.event_type!r} "
            f"incident={self.incident_id}>"
        )

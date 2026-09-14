"""
SLA Rule ORM model.

Maps an Authority + Issue Type to an SLA resolution window (in hours).
This replaces the legacy Priority-based SLA tier lookup.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.authority import Authority


class SLARule(Base):
    """
    SLA rule determining resolution deadline and escalation parameters
    for a specific issue type under an authority.
    """

    __tablename__ = "sla_rules"

    authority_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("authorities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_grace_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationship
    authority: Mapped["Authority"] = relationship("Authority", back_populates="sla_rules")

    __table_args__ = (
        UniqueConstraint("authority_id", "issue_type", name="uq_sla_rules_authority_issue_type"),
        CheckConstraint("resolution_hours > 0", name="ck_sla_rules_resolution_hours_positive"),
        CheckConstraint("escalation_grace_hours >= 0", name="ck_sla_rules_escalation_grace_hours_non_negative"),
    )

    def __repr__(self) -> str:
        return (
            f"<SLARule id={self.id} authority_id={self.authority_id} "
            f"issue_type={self.issue_type!r} hours={self.resolution_hours}>"
        )

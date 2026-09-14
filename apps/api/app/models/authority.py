"""
Authority ORM model.

Represents a civic agency responsible for resolving incidents within
a jurisdiction (e.g. "City Roads Department", "Water Utility").

Authorities define their own SLA tiers (standard / priority / emergency)
which determine how quickly incidents must be resolved.

An Authority has zero or more Jurisdictions. An Authority can cover
multiple geographic regions (e.g. a state-level agency).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.jurisdiction import Jurisdiction
    from app.models.incident import Incident
    from app.models.user import User
    from app.models.sla_rule import SLARule


class Authority(Base):
    """
    Civic authority responsible for resolving incidents.

    SLA windows (in hours) represent the maximum allowed resolution time
    per priority tier. The accountability engine uses these to compute
    due dates and transition accountability states.
    """

    __tablename__ = "authorities"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact
    contact_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # SLA tiers (hours per priority level)
    # ------------------------------------------------------------------
    # How many hours to resolve a LOW priority incident
    sla_hours_low: Mapped[int] = mapped_column(Integer, nullable=False, default=168)    # 1 week
    # MEDIUM priority
    sla_hours_medium: Mapped[int] = mapped_column(Integer, nullable=False, default=72)  # 3 days
    # HIGH priority
    sla_hours_high: Mapped[int] = mapped_column(Integer, nullable=False, default=24)    # 1 day
    # CRITICAL priority
    sla_hours_critical: Mapped[int] = mapped_column(Integer, nullable=False, default=4) # 4 hours

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    jurisdictions: Mapped[list["Jurisdiction"]] = relationship(
        "Jurisdiction", back_populates="authority"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="authority"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="authority"
    )
    sla_rules: Mapped[list["SLARule"]] = relationship(
        "SLARule", back_populates="authority", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Authority id={self.id} code={self.short_code!r}>"

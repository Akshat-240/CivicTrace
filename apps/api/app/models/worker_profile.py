import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.authority import Authority
    from app.models.incident import Incident

class WorkerProfile(Base):
    __tablename__ = 'worker_profiles'

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False
    )
    authority_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey('authorities.id', ondelete='CASCADE'), nullable=False
    )
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="worker_profile")
    authority: Mapped["Authority"] = relationship("Authority", back_populates="workers")
    assigned_incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="assigned_worker")

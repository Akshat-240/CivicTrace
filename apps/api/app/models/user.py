'''
User ORM model.
'''
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.authority import Authority

class User(Base):
    '''Application user model.'''

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name='userrole', native_enum=False, length=30),
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    authority_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey('authorities.id', ondelete='SET NULL'), nullable=True
    )

    authority: Mapped[Optional['Authority']] = relationship('Authority', back_populates='users')

    __table_args__ = (
        CheckConstraint(
            """
            (role IN ('CITIZEN', 'ADMIN') AND authority_id IS NULL)
            OR (role = 'AUTHORITY' AND authority_id IS NOT NULL)
            """,
            name='users_role_authority_check'
        ),
    )

    def __repr__(self) -> str:
        return f'<User id={self.id} email={self.email!r} role={self.role}>'

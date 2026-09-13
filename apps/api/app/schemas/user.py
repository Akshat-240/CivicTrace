import uuid
import re
from typing import Optional
from pydantic import BaseModel, validator, Field

from app.models.enums import UserRole

def validate_email(v: str) -> str:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
        raise ValueError("Invalid email address")
    return v.lower()

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.CITIZEN
    authority_id: Optional[uuid.UUID] = None

    @validator('email')
    def email_validator(cls, v):
        return validate_email(v)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    authority_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

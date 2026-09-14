import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.dependencies import DbSession, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.enums import UserRole
from app.models.authority import Authority
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: DbSession):
    # Enforce CITIZEN role
    if user_in.role in (UserRole.ADMIN, UserRole.AUTHORITY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot create ADMIN or AUTHORITY accounts."
        )
    
    # Enforce no authority_id
    if user_in.authority_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot assign authority_id."
        )
    
    # Check duplicate email
    normalized_email = user_in.email.lower()
    stmt = select(User).where(User.email == normalized_email)
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
        
    from datetime import datetime, timezone

    new_user = User(
        email=normalized_email,
        hashed_password=hash_password(user_in.password),
        role=UserRole.CITIZEN,
        authority_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession
):
    normalized_email = form_data.username.lower()
    stmt = select(User).where(User.email == normalized_email)
    user = await db.scalar(stmt)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value}
    )
    
    return Token(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user

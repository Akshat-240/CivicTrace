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

@router.get("/authorities", summary="Get all authorities for registration")
async def get_authorities(db: DbSession):
    from app.models.authority import Authority
    from sqlalchemy import select
    stmt = select(Authority)
    authorities = await db.scalars(stmt)
    return [{"id": str(a.id), "name": a.name} for a in authorities]


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: DbSession):
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

    auth_id = user_in.authority_id
    if user_in.role in (UserRole.AUTHORITY, UserRole.FIELD_WORKER) and auth_id is None:
        from app.models.authority import Authority
        stmt_auth = select(Authority).limit(1)
        first_auth = await db.scalar(stmt_auth)
        if first_auth:
            auth_id = first_auth.id

    new_user = User(
        full_name=user_in.full_name,
        email=normalized_email,
        city=user_in.city,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        authority_id=auth_id,
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

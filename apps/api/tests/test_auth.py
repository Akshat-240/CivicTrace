
import pytest
from sqlalchemy.exc import IntegrityError
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.enums import UserRole
from app.models.authority import Authority
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from jose import JWTError

@pytest.fixture
async def valid_authority(db_session: AsyncSession):
    auth = Authority(
        name="Test Auth",
        short_code="TST-AUTH",
        sla_hours_low=10,
        sla_hours_medium=5,
        sla_hours_high=2,
        sla_hours_critical=1
    )
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    return auth

@pytest.mark.asyncio
async def test_password_hashing():
    pwd = "my_secure_password"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong_password", hashed)

@pytest.mark.asyncio
async def test_jwt_creation_and_decode():
    token = create_access_token(subject="user123", extra_claims={"role": "citizen"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["role"] == "citizen"

@pytest.mark.asyncio
async def test_citizen_registration_success(async_client: AsyncClient, db_session: AsyncSession):
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "citizen@example.com",
        "password": "password123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "citizen@example.com"
    assert data["role"] == "citizen"
    assert "hashed_password" not in data

    # check db
    stmt = select(User).where(User.email == "citizen@example.com")
    user = await db_session.scalar(stmt)
    assert user is not None
    assert verify_password("password123", user.hashed_password)

@pytest.mark.asyncio
async def test_duplicate_email_rejected(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = await async_client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_public_registration_cannot_create_admin(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "admin@example.com",
        "password": "password123",
        "role": "admin"
    })
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_public_registration_cannot_create_authority(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "auth@example.com",
        "password": "password123",
        "role": "authority"
    })
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "password"})
    resp = await async_client.post("/api/v1/auth/token", data={
        "username": "login@example.com",
        "password": "password"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_login_wrong_credentials(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"email": "login2@example.com", "password": "password"})
    resp = await async_client.post("/api/v1/auth/token", data={
        "username": "login2@example.com",
        "password": "wrongpassword"
    })
    assert resp.status_code == 401

    resp2 = await async_client.post("/api/v1/auth/token", data={
        "username": "nonexistent@example.com",
        "password": "password"
    })
    assert resp2.status_code == 401

@pytest.mark.asyncio
async def test_inactive_user_cannot_login(async_client: AsyncClient, db_session: AsyncSession):
    resp = await async_client.post("/api/v1/auth/register", json={"email": "inactive@example.com", "password": "password"})
    user_id = resp.json()["id"]

    # manually deactivate
    stmt = select(User).where(User.id == user_id)
    user = await db_session.scalar(stmt)
    user.is_active = False
    await db_session.commit()

    resp = await async_client.post("/api/v1/auth/token", data={
        "username": "inactive@example.com",
        "password": "password"
    })
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_requires_auth(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_returns_profile(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"email": "me@example.com", "password": "password"})
    token_resp = await async_client.post("/api/v1/auth/token", data={"username": "me@example.com", "password": "password"})
    token = token_resp.json()["access_token"]

    me_resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "me@example.com"
    assert me_resp.json()["role"] == "citizen"

@pytest.mark.asyncio
async def test_invalid_jwt_returns_401(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_nonexistent_user_returns_401(async_client: AsyncClient):
    token = create_access_token(subject="00000000-0000-0000-0000-000000000000")
    resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_inactive_auth_me_returns_401(async_client: AsyncClient, db_session: AsyncSession):
    await async_client.post("/api/v1/auth/register", json={"email": "inactive_me@example.com", "password": "password"})
    token_resp = await async_client.post("/api/v1/auth/token", data={"username": "inactive_me@example.com", "password": "password"})
    token = token_resp.json()["access_token"]

    # manually deactivate
    stmt = select(User).where(User.email == "inactive_me@example.com")
    user = await db_session.scalar(stmt)
    user.is_active = False
    await db_session.commit()

    me_resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401

@pytest.mark.asyncio
async def test_stale_jwt_role_overridden_by_db(async_client: AsyncClient, db_session: AsyncSession):
    await async_client.post("/api/v1/auth/register", json={"email": "stale@example.com", "password": "password"})
    token_resp = await async_client.post("/api/v1/auth/token", data={"username": "stale@example.com", "password": "password"})
    token = token_resp.json()["access_token"]

    # decode to prove token says citizen
    payload = decode_access_token(token)
    assert payload["role"] == "citizen"

    # manual role update
    stmt = select(User).where(User.email == "stale@example.com")
    user = await db_session.scalar(stmt)
    user.role = UserRole.ADMIN
    await db_session.commit()

    # auth/me should return admin
    me_resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "admin"

@pytest.mark.asyncio
async def test_public_registration_cannot_assign_authority(async_client: AsyncClient, valid_authority):
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "hacker@example.com",
        "password": "password123",
        "authority_id": str(valid_authority.id)
    })
    assert resp.status_code == 403


from fastapi import HTTPException
from app.api.dependencies import require_role

@pytest.mark.asyncio
async def test_correct_rbac_role_allowed(db_session: AsyncSession):
    user = User(email="ok@example.com", hashed_password="pw", role=UserRole.ADMIN)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    dep = require_role(UserRole.ADMIN)
    result = dep(user)
    assert result.id == user.id

@pytest.mark.asyncio
async def test_wrong_rbac_role_rejected(db_session: AsyncSession):
    user = User(email="bad@example.com", hashed_password="pw", role=UserRole.CITIZEN)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    dep = require_role(UserRole.ADMIN)
    try:
        dep(user)
        assert False, "Should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
@pytest.mark.asyncio
async def test_valid_authority_association(db_session: AsyncSession, valid_authority: Authority):
    user = User(
        email="auth_officer@example.com",
        hashed_password="hash",
        role=UserRole.AUTHORITY,
        authority_id=valid_authority.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.authority_id == valid_authority.id

@pytest.mark.asyncio
async def test_invalid_authority_id(db_session: AsyncSession):
    import uuid
    user = User(
        email="bad_auth@example.com",
        hashed_password="hash",
        role=UserRole.AUTHORITY,
        authority_id=uuid.uuid4()
    )
    db_session.add(user)
    try:
        await db_session.commit()
        assert False, "Should have failed FK constraint"
    except IntegrityError:
        await db_session.rollback()

@pytest.mark.asyncio
async def test_admin_cannot_receive_authority_id(db_session: AsyncSession, valid_authority: Authority):
    user = User(
        email="admin_with_auth@example.com",
        hashed_password="hash",
        role=UserRole.ADMIN,
        authority_id=valid_authority.id
    )
    db_session.add(user)
    try:
        await db_session.commit()
        assert False, "Should have failed CHECK constraint"
    except IntegrityError:
        await db_session.rollback()

@pytest.mark.asyncio
async def test_malformed_jwt_subject_returns_401(async_client: AsyncClient):
    from app.core.security import create_access_token
    token = create_access_token(subject="not-a-valid-uuid")
    resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_public_registration_admin_with_authority_id_rejected(async_client: AsyncClient, valid_authority):
    # Tests that attempting to pass role=ADMIN and authority_id both get rejected properly (403)
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "hax0r@example.com",
            "password": "password123",
            "role": "admin",
            "authority_id": str(valid_authority.id)
        }
    )
    assert resp.status_code == 403

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.user import User
from app.models.authority import Authority
from app.models.worker_profile import WorkerProfile
from app.models.jurisdiction import Jurisdiction
from app.models.enums import UserRole, IncidentStatus, WorkerTaskStatus
from app.models.incident import Incident
from app.core.security import hash_password
import uuid
import io
from unittest.mock import patch

@pytest.fixture
async def setup_worker_data(db_session: AsyncSession):
    auth_id = uuid.uuid4()
    auth = Authority(id=auth_id, name='Test Auth', short_code='TA')
    db_session.add(auth)

    jur_id = uuid.uuid4()
    jur = Jurisdiction(id=jur_id, name='Test Jur', code='TJ', authority_id=auth_id)
    db_session.add(jur)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="test_worker@lucknow.gov.in",
        hashed_password=hash_password("password"),
        role=UserRole.FIELD_WORKER,
        authority_id=auth_id
    )
    db_session.add(user)

    worker_id = uuid.uuid4()
    prof = WorkerProfile(id=worker_id, user_id=user_id, authority_id=auth_id)
    db_session.add(prof)

    inc_id = uuid.uuid4()
    inc = Incident(
        id=inc_id,
        reference_number="INC-WORKER-1",
        title="Test worker task",
        authority_id=auth_id,
        jurisdiction_id=jur_id,
        status=IncidentStatus.ACTIVE,
        worker_status=WorkerTaskStatus.ASSIGNED,
        assigned_worker_id=worker_id,
        issue_type="road_hazard"
    )
    db_session.add(inc)

    await db_session.commit()

    return {"user": user, "incident": inc, "password": "password"}

@pytest.mark.asyncio
async def test_worker_flow(async_client: AsyncClient, setup_worker_data):
    data = setup_worker_data

    # 1. Login
    res = await async_client.post("/api/v1/auth/token", data={
        "username": data["user"].email,
        "password": data["password"]
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Tasks
    res = await async_client.get("/api/v1/worker/tasks", headers=headers)
    assert res.status_code == 200, res.text
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == str(data["incident"].id)

    # 3. Get Task Detail
    res = await async_client.get(f"/api/v1/worker/tasks/{data['incident'].id}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["title"] == "Test worker task"

    # 4. Update Status (Assigned -> Accepted -> On the way -> At Location -> In Progress)
    for st in ["ACCEPTED", "ON_THE_WAY", "AT_LOCATION", "IN_PROGRESS"]:
        res = await async_client.patch(f"/api/v1/worker/tasks/{data['incident'].id}/status", json={"status": st}, headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["worker_status"] == st

    # 5. Submit Resolution
    file_bytes = b"dummy resolution image"
    files = {"file": ("after.jpg", io.BytesIO(file_bytes), "image/jpeg")}
    data_payload = {
        "notes": "All fixed!",
        "latitude": "26.123",
        "longitude": "80.123", "capture_timestamp": "2026-09-14T10:00:00Z"
    }

    res = await async_client.post(
        f"/api/v1/worker/tasks/{data['incident'].id}/submit-resolution",
        files=files,
        data=data_payload,
        headers=headers
    )
    assert res.status_code == 200, res.text

    # Verify DB
    res = await async_client.get(f"/api/v1/worker/tasks/{data['incident'].id}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["worker_status"] == "COMPLETED"
    assert res.json()["status"] == "under_review"



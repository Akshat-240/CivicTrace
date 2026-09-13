"""
Unit and API integration tests for the Evidence Upload endpoint.
Covers requirements A through N with mocked StorageService / HTTP layer.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ServiceUnavailableError
from app.models.enums import EvidenceStatus, EvidenceType, IncidentStatus
from app.models.incident import Incident
from app.services.storage_service import (
    MAX_FILE_SIZE_BYTES,
    StorageMetadata,
    StorageService,
)


@pytest.fixture
async def active_incident(async_client: AsyncClient) -> dict:
    """Creates a fresh test incident via the API."""
    res = await async_client.post(
        "/api/v1/incidents",
        json={
            "title": "Pothole on 5th Avenue",
            "issue_type": "pothole",
            "description": "Deep pothole causing vehicle damage",
        },
    )
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# Test Cases A through N
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_evidence_upload(async_client: AsyncClient, active_incident: dict):
    """
    Case A, K, L, N:
    - Successful upload
    - Correct storage metadata stored
    - Starts in PENDING state
    - No AI processing triggered
    """
    inc_id = active_incident["id"]
    file_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00"

    fake_meta = StorageMetadata(
        storage_key=f"evidence/{inc_id}/mock-ev-id/pothole.jpg",
        bucket="evidence",
        file_size_bytes=len(file_bytes),
        mime_type="image/jpeg",
    )

    with patch.object(StorageService, "upload_object", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = fake_meta

        response = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence/upload",
            files={"file": ("pothole.jpg", file_bytes, "image/jpeg")},
            data={"description": "Close-up photo of pothole"},
        )

        assert response.status_code == 201
        data = response.json()

        # Check evidence ID and incident link
        assert "id" in data
        assert data["incident_id"] == inc_id
        assert data["evidence_type"] == EvidenceType.IMAGE.value
        assert data["description"] == "Close-up photo of pothole"

        # Check metadata persistence
        assert data["mime_type"] == "image/jpeg"
        assert data["file_size_bytes"] == len(file_bytes)

        # Check initial state and no AI processing
        assert data["status"] == EvidenceStatus.PENDING.value
        assert data["ai_category"] is None
        assert data["ai_confidence"] is None
        assert data["ai_safety_risk"] is None
        assert data["ai_ambiguity_flag"] is False

        # StorageService upload was called
        mock_upload.assert_called_once()


@pytest.mark.asyncio
async def test_upload_missing_incident(async_client: AsyncClient):
    """Case B: Missing incident returns 404."""
    fake_id = str(uuid.uuid4())
    file_bytes = b"sample image bytes"

    response = await async_client.post(
        f"/api/v1/incidents/{fake_id}/evidence/upload",
        files={"file": ("sample.jpg", file_bytes, "image/jpeg")},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_upload_invalid_mime_type(async_client: AsyncClient, active_incident: dict):
    """Case C: Unsupported MIME type rejected with 422."""
    inc_id = active_incident["id"]
    file_bytes = b"%PDF-1.4 header"

    response = await async_client.post(
        f"/api/v1/incidents/{inc_id}/evidence/upload",
        files={"file": ("document.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Unsupported MIME type" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_upload_empty_file(async_client: AsyncClient, active_incident: dict):
    """Case D: 0-byte file rejected with 422."""
    inc_id = active_incident["id"]

    response = await async_client.post(
        f"/api/v1/incidents/{inc_id}/evidence/upload",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "File content is empty" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_upload_oversized_file(async_client: AsyncClient, active_incident: dict):
    """Case E: File exceeding 50 MB rejected with 422."""
    inc_id = active_incident["id"]
    oversized = b"x" * (MAX_FILE_SIZE_BYTES + 10)

    response = await async_client.post(
        f"/api/v1/incidents/{inc_id}/evidence/upload",
        files={"file": ("huge.jpg", oversized, "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "exceeds maximum limit of 50 MB" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_upload_malformed_multipart_input(async_client: AsyncClient, active_incident: dict):
    """Case F: Missing file payload returns 422."""
    inc_id = active_incident["id"]

    response = await async_client.post(
        f"/api/v1/incidents/{inc_id}/evidence/upload",
        data={"description": "No file included"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upload_storage_failure(async_client: AsyncClient, active_incident: dict):
    """Case G: Supabase upload failure translates to 503 Service Unavailable."""
    inc_id = active_incident["id"]
    file_bytes = b"valid image content"

    with patch.object(StorageService, "upload_object", new_callable=AsyncMock) as mock_upload:
        mock_upload.side_effect = ServiceUnavailableError("Storage service request timed out during upload.")

        response = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence/upload",
            files={"file": ("test.png", file_bytes, "image/png")},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_upload_database_failure_triggers_storage_compensation(
    async_client: AsyncClient, active_incident: dict
):
    """
    Case H & I:
    Database persistence failure after storage upload must invoke compensation cleanup
    via StorageService.delete_object(storage_key).
    """
    inc_id = active_incident["id"]
    file_bytes = b"valid image content"
    target_key = f"evidence/{inc_id}/ev123/test.png"

    fake_meta = StorageMetadata(
        storage_key=target_key,
        bucket="evidence",
        file_size_bytes=len(file_bytes),
        mime_type="image/png",
    )

    with patch.object(StorageService, "upload_object", new_callable=AsyncMock) as mock_upload, \
         patch.object(StorageService, "delete_object", new_callable=AsyncMock) as mock_delete, \
         patch("app.repositories.evidence_repo.EvidenceRepository.create", new_callable=AsyncMock) as mock_repo_create:

        mock_upload.return_value = fake_meta
        mock_repo_create.side_effect = RuntimeError("Simulated Database Crash")

        response = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence/upload",
            files={"file": ("test.png", file_bytes, "image/png")},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"

        # Verify upload happened
        mock_upload.assert_called_once()
        # Verify compensation cleanup was executed with the generated key
        assert mock_delete.call_count == 1
        deleted_key = mock_delete.call_args[0][0]
        assert deleted_key.startswith(f"evidence/{inc_id}/")
        assert deleted_key.endswith("/test.png")


@pytest.mark.asyncio
async def test_upload_safe_filename_handling(async_client: AsyncClient, active_incident: dict):
    """Case J: Path traversal attempts in filename are sanitized."""
    inc_id = active_incident["id"]
    file_bytes = b"safe image content"

    captured_storage_key = None

    async def fake_upload(storage_key, content, mime_type, upsert=False):
        nonlocal captured_storage_key
        captured_storage_key = storage_key
        return StorageMetadata(
            storage_key=storage_key,
            bucket="evidence",
            file_size_bytes=len(content),
            mime_type=mime_type,
        )

    with patch.object(StorageService, "upload_object", side_effect=fake_upload):
        response = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence/upload",
            files={"file": ("../../../../etc/passwd", file_bytes, "image/jpeg")},
        )
        assert response.status_code == 201
        assert captured_storage_key is not None
        # Must not contain path traversal tokens
        assert ".." not in captured_storage_key
        assert "/etc/passwd" not in captured_storage_key
        assert captured_storage_key.endswith("/passwd")


@pytest.mark.asyncio
async def test_upload_with_location_metadata(async_client: AsyncClient, active_incident: dict):
    """Case M: Location coordinates and address persisted correctly."""
    inc_id = active_incident["id"]
    file_bytes = b"location photo content"

    with patch.object(StorageService, "upload_object", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = StorageMetadata(
            storage_key=f"evidence/{inc_id}/loc_ev/pothole.jpg",
            bucket="evidence",
            file_size_bytes=len(file_bytes),
            mime_type="image/jpeg",
        )

        response = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence/upload",
            files={"file": ("pothole.jpg", file_bytes, "image/jpeg")},
            data={
                "latitude": "12.9716",
                "longitude": "77.5946",
                "accuracy_meters": "5.0",
                "address_raw": "MG Road, Bengaluru",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["location"] is not None
        assert abs(data["location"]["latitude"] - 12.9716) < 1e-4
        assert abs(data["location"]["longitude"] - 77.5946) < 1e-4
        assert data["location"]["address_raw"] == "MG Road, Bengaluru"


@pytest.mark.asyncio
async def test_upload_rejects_closed_incident(async_client: AsyncClient, db_session: AsyncSession):
    """Case O: Incidents in terminal state (RESOLVED, CLOSED) reject uploads with 409 Conflict."""
    # Create incident in closed state directly
    closed_inc = Incident(
        reference_number="INC-CLOSED",
        status=IncidentStatus.RESOLVED,
        title="Already Resolved Incident",
    )
    db_session.add(closed_inc)
    await db_session.commit()
    await db_session.refresh(closed_inc)

    file_bytes = b"sample image"
    response = await async_client.post(
        f"/api/v1/incidents/{closed_inc.id}/evidence/upload",
        files={"file": ("photo.jpg", file_bytes, "image/jpeg")},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"
    assert "cannot accept new evidence" in response.json()["error"]["message"]

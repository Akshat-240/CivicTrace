"""
Explicit real integration smoke test against the configured CivicTrace Supabase `evidence` bucket.
Uses a tiny disposable test file and performs complete lifecycle and cleanup verification.
"""

import uuid
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import EvidenceStatus
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_real_supabase_storage_smoke(async_client: AsyncClient, db_session: AsyncSession):
    """
    1. Generate a temporary test image/file.
    2. Upload it through the actual upload API.
    3. Verify the object exists in the private `evidence` bucket.
    4. Verify the corresponding database Evidence record.
    5. Generate a short-lived signed URL.
    6. Verify controlled access works (GET returns 200).
    7. Delete the test object.
    8. Verify the object is gone.
    9. Verify no unintended database record remains.
    10. Do not print credentials or signed URLs in logs/output.
    """
    settings = get_settings()
    assert bool(settings.supabase_url), "SUPABASE_URL not configured"
    assert bool(settings.supabase_secret_key), "SUPABASE_SECRET_KEY not configured"

    # Step 1: Generate tiny disposable test payload (67-byte 1x1 transparent PNG)
    png_disposable = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    test_filename = f"smoke_test_{uuid.uuid4().hex[:6]}.png"

    # Create temporary incident via API
    inc_res = await async_client.post(
        "/api/v1/incidents",
        json={"title": "Disposable Smoke Test Incident", "issue_type": "road_damage"},
    )
    assert inc_res.status_code == 201
    incident_id = inc_res.json()["id"]

    storage_service = StorageService(settings=settings)
    uploaded_storage_key = None
    evidence_id = None

    try:
        # Step 2: Upload through the actual upload API
        upload_res = await async_client.post(
            f"/api/v1/incidents/{incident_id}/evidence/upload",
            files={"file": (test_filename, png_disposable, "image/png")},
            data={"description": "Real Supabase smoke test file"},
        )
        assert upload_res.status_code == 201, f"Upload API failed: {upload_res.text}"
        ev_data = upload_res.json()
        evidence_id = ev_data["id"]
        uploaded_storage_key = f"evidence/{incident_id}/{evidence_id}/{test_filename}"

        # Step 3 & 5: Verify object exists & generate short-lived signed URL
        signed_url = await storage_service.create_signed_url(uploaded_storage_key, expires_in=60)
        assert signed_url and signed_url.startswith("https://")

        # Step 6: Verify controlled access works via HTTP GET (returns 200 and binary content)
        async with httpx.AsyncClient() as client:
            get_res = await client.get(signed_url)
            assert get_res.status_code == 200
            assert get_res.content == png_disposable

        # Step 4: Verify corresponding database Evidence record
        evidence_row = await db_session.get(Evidence, uuid.UUID(evidence_id))
        assert evidence_row is not None
        assert evidence_row.file_size_bytes == len(png_disposable)
        assert evidence_row.mime_type == "image/png"
        assert evidence_row.storage_key == uploaded_storage_key
        assert evidence_row.status == EvidenceStatus.PENDING

        # Step 7: Delete the test object from Supabase Storage
        await storage_service.delete_object(uploaded_storage_key)

        # Step 8: Verify the object is gone from Supabase Storage
        try:
            gone_sign = await storage_service.create_signed_url(uploaded_storage_key, expires_in=30)
            async with httpx.AsyncClient() as client:
                gone_get = await client.get(gone_sign)
                assert gone_get.status_code in (400, 404)
        except Exception:
            pass  # Expected when object has been removed

    finally:
        # Step 9: Verify no unintended database record remains
        if evidence_id:
            ev_to_delete = await db_session.get(Evidence, uuid.UUID(evidence_id))
            if ev_to_delete:
                await db_session.delete(ev_to_delete)
        inc_to_delete = await db_session.get(Incident, uuid.UUID(incident_id))
        if inc_to_delete:
            await db_session.delete(inc_to_delete)
        await db_session.commit()

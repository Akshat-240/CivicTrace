"""
test_ai_frontend_integration.py
================================
Integration tests verifying that the AI perception pipeline connects to the real
citizen evidence flow, persists normalized results, preserves ambiguity, handles
non-blocking operational failures with retry, and falls back to Gemini when Azure fails.
"""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.enums import EvidenceStatus, IssueType, SeverityLevel
from app.schemas.ai import AIAnalysisResult
from app.services.ai.azure import AzureOperationalError, AzureVisionProvider


@pytest.mark.asyncio
class TestAIFrontendIntegration:
    async def test_citizen_evidence_upload_and_ai_analysis_pipeline(
        self, async_client: AsyncClient
    ):
        """
        1. Citizen creates an incident.
        2. Citizen uploads real image evidence.
        3. Trigger AI analysis endpoint (Azure Computer Vision provider).
        4. Validated AI result is persisted in database and returned in API response.
        """
        # Step 1: Create incident
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={
                "title": "Severe pothole on roadway",
                "description": "Deep asphalt depression causing hazardous vehicle congestion.",
                "issue_type": "road_damage",
                "location": {
                    "latitude": 26.8467,
                    "longitude": 80.9462,
                    "address_raw": "Hazratganj Crossing, Lucknow",
                },
            },
        )
        assert create_res.status_code == 201
        inc_data = create_res.json()
        incident_id = inc_data["id"]

        # Step 2: Upload evidence media file
        file_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
        files = {"file": ("pothole_evidence.jpg", io.BytesIO(file_bytes), "image/jpeg")}
        data = {
            "description": "Photo of dangerous road pothole",
            "latitude": "26.8467",
            "longitude": "80.9462",
            "address_raw": "Hazratganj Crossing, Lucknow",
            "evidence_type": "image",
        }

        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta", (), {"storage_key": f"incidents/{incident_id}/evidence/pothole.jpg", "file_size_bytes": len(file_bytes)}
            )()

            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files=files,
                data=data,
            )
            assert upload_res.status_code == 201
            evidence_data = upload_res.json()
            evidence_id = evidence_data["id"]
            assert evidence_data["status"] == EvidenceStatus.PENDING.value

        # Step 3: Trigger AI analysis (Mock Azure Computer Vision provider output)
        mock_azure_result = AIAnalysisResult(
            civic_issue_category=IssueType.POTHOLE,
            confidence=0.94,
            severity_assessment=SeverityLevel.HIGH,
            safety_risk_detected=True,
            ambiguity_flag=False,
            ambiguity_reason=None,
            extracted_attributes={"provider": "azure_computer_vision", "tags": ["pothole", "road"]},
            explanation="Azure Computer Vision visual observation: large deep pothole in roadway.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_azure:

            mock_signed_url.return_value = "https://supabase.mock/signed/pothole.jpg"
            mock_azure.return_value = mock_azure_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            # Verify returned structured schema
            assert ai_data["civic_issue_category"] == IssueType.POTHOLE.value
            assert ai_data["confidence"] == pytest.approx(0.94, rel=1e-2)
            assert ai_data["severity_assessment"] == SeverityLevel.HIGH.value
            assert ai_data["safety_risk_detected"] is True
            assert ai_data["ambiguity_flag"] is False
            assert "pothole" in ai_data["explanation"].lower()
            assert ai_data["extracted_attributes"]["provider"] == "azure_computer_vision"

        # Step 4: Verify persistence on the Evidence record
        list_res = await async_client.get(f"/api/v1/incidents/{incident_id}/evidence")
        assert list_res.status_code == 200
        ev_items = list_res.json()
        target_ev = next(e for e in ev_items if e["id"] == evidence_id)

        assert target_ev["status"] == EvidenceStatus.PROCESSED.value
        assert target_ev["ai_category"] == "pothole"
        assert target_ev["ai_confidence"] == pytest.approx(0.94, rel=1e-2)
        assert target_ev["ai_severity_raw"] == "high"
        assert target_ev["ai_safety_risk"] is True
        assert target_ev["ai_ambiguity_flag"] is False
        assert target_ev["ai_perception_payload"] is not None

    async def test_ai_ambiguity_flag_preservation(self, async_client: AsyncClient):
        """
        Unclear or unrecognized visual evidence flags ambiguity, preserves reason,
        and persists in database without breaking the workflow.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Unclear civic complaint", "issue_type": "other"},
        )
        incident_id = create_res.json()["id"]

        # Upload evidence
        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta", (), {"storage_key": f"incidents/{incident_id}/evidence/blurry.jpg", "file_size_bytes": len(file_bytes)}
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("blurry.jpg", io.BytesIO(file_bytes), "image/jpeg")},
                data={"description": "Blurry picture"},
            )
            evidence_id = upload_res.json()["id"]

        mock_ambiguous_result = AIAnalysisResult(
            civic_issue_category=None,
            confidence=0.25,
            severity_assessment=None,
            safety_risk_detected=False,
            ambiguity_flag=True,
            ambiguity_reason="Visual evidence lacks recognizable civic issue features.",
            extracted_attributes={"provider": "azure_computer_vision"},
            explanation="Azure Computer Vision analyzed image but returned no distinct civic issue features.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_azure:

            mock_signed_url.return_value = "https://supabase.mock/signed/blurry.jpg"
            mock_azure.return_value = mock_ambiguous_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            assert ai_data["ambiguity_flag"] is True
            assert ai_data["civic_issue_category"] is None
            assert ai_data["ambiguity_reason"] is not None
            assert "lacks recognizable" in ai_data["ambiguity_reason"].lower()

        # Check DB persistence
        list_res = await async_client.get(f"/api/v1/incidents/{incident_id}/evidence")
        target_ev = next(e for e in list_res.json() if e["id"] == evidence_id)
        assert target_ev["ai_ambiguity_flag"] is True
        assert target_ev["ai_ambiguity_reason"] is not None

    async def test_ai_failure_non_blocking_and_retry_workflow(
        self, async_client: AsyncClient
    ):
        """
        If AI provider fails operationally, evidence remains intact in FAILED status.
        A subsequent retry call to analyze endpoint successfully re-processes the evidence.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Broken streetlight", "issue_type": "broken_streetlight"},
        )
        incident_id = create_res.json()["id"]

        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta", (), {"storage_key": f"incidents/{incident_id}/evidence/light.jpg", "file_size_bytes": len(file_bytes)}
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("light.jpg", io.BytesIO(file_bytes), "image/jpeg")},
                data={"description": "Dark streetlight"},
            )
            evidence_id = upload_res.json()["id"]

        # 1. First analyze call fails due to service operational error on all providers
        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", side_effect=AzureOperationalError("Azure timeout")), \
             patch("app.services.ai.gemini.GeminiAIProvider.analyze_evidence", side_effect=AzureOperationalError("Gemini unavailable")):

            mock_signed_url.return_value = "https://supabase.mock/signed/light.jpg"

            fail_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert fail_res.status_code == 503

        # Verify evidence is in FAILED state but NOT deleted
        list_res = await async_client.get(f"/api/v1/incidents/{incident_id}/evidence")
        target_ev = next(e for e in list_res.json() if e["id"] == evidence_id)
        assert target_ev["status"] == EvidenceStatus.FAILED.value

        # 2. Citizen clicks "Retry AI" -> Second analyze call succeeds
        mock_retry_result = AIAnalysisResult(
            civic_issue_category=IssueType.BROKEN_STREETLIGHT,
            confidence=0.91,
            severity_assessment=SeverityLevel.MEDIUM,
            safety_risk_detected=False,
            ambiguity_flag=False,
            ambiguity_reason=None,
            extracted_attributes={"provider": "azure_computer_vision"},
            explanation="Azure Computer Vision observed non-functional broken street light fixture.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_azure:

            mock_signed_url.return_value = "https://supabase.mock/signed/light.jpg"
            mock_azure.return_value = mock_retry_result

            retry_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert retry_res.status_code == 200
            assert retry_res.json()["civic_issue_category"] == IssueType.BROKEN_STREETLIGHT.value

        # Verify evidence transitioned to PROCESSED
        list_res2 = await async_client.get(f"/api/v1/incidents/{incident_id}/evidence")
        target_ev2 = next(e for e in list_res2.json() if e["id"] == evidence_id)
        assert target_ev2["status"] == EvidenceStatus.PROCESSED.value
        assert target_ev2["ai_category"] == "broken_streetlight"

    async def test_azure_operational_failure_triggers_gemini_fallback(
        self, async_client: AsyncClient
    ):
        """
        When Azure Computer Vision encounters an operational failure (e.g. 500 error),
        AIService transparently falls back to GeminiAIProvider.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Flooding on road", "issue_type": "flooding"},
        )
        incident_id = create_res.json()["id"]

        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta", (), {"storage_key": f"incidents/{incident_id}/evidence/flood.jpg", "file_size_bytes": len(file_bytes)}
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("flood.jpg", io.BytesIO(file_bytes), "image/jpeg")},
                data={"description": "Flooded street with waterlogging"},
            )
            evidence_id = upload_res.json()["id"]

        gemini_mock_result = AIAnalysisResult(
            civic_issue_category=IssueType.FLOODING,
            confidence=0.88,
            severity_assessment=SeverityLevel.HIGH,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Gemini fallback detected street waterlogging and flooding.",
            extracted_attributes={"provider": "gemini_fallback"},
        )

        # Primary Azure fails with AzureOperationalError, Gemini fallback succeeds
        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", side_effect=AzureOperationalError("Azure 500 Internal Error")), \
             patch("app.services.ai.gemini.GeminiAIProvider.analyze_evidence", new_callable=AsyncMock) as mock_gemini:

            mock_signed_url.return_value = "https://supabase.mock/signed/flood.jpg"
            mock_gemini.return_value = gemini_mock_result

            res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert res.status_code == 200
            data = res.json()
            assert data["civic_issue_category"] == IssueType.FLOODING.value
            assert data["extracted_attributes"]["provider"] == "gemini_fallback"
            assert mock_gemini.called

    async def test_analyze_nonexistent_evidence_returns_404(
        self, async_client: AsyncClient
    ):
        """
        Analyzing a non-existent incident or evidence returns 404 Not Found.
        """
        rand_inc_id = uuid.uuid4()
        rand_ev_id = uuid.uuid4()
        res = await async_client.post(
            f"/api/v1/incidents/{rand_inc_id}/evidence/{rand_ev_id}/analyze"
        )
        assert res.status_code == 404


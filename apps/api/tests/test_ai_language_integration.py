"""
test_ai_language_integration.py
================================
Integration tests verifying multi-modal perception:
- Image + written briefing combining Azure Computer Vision and Azure AI Language.
- Image only / empty briefing skipping Language without error.
- Non-blocking Language operational failure preserving Vision perception.
- Vision/Language conflict handling preserving ambiguity without overriding Vision.
- End-to-end voice transcription into citizen briefing and multi-modal perception.
"""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.enums import EvidenceStatus, IssueType, SeverityLevel
from app.schemas.ai import (
    AIAnalysisResult,
    LanguagePerceptionResult,
    SpeechTranscriptionResponse,
    VisualPerceptionResult,
)
from app.services.ai.language import AzureLanguageOperationalError


@pytest.mark.asyncio
class TestAILanguageIntegration:
    async def test_image_and_written_briefing_multi_modal_perception(
        self, async_client: AsyncClient
    ):
        """
        Citizen uploads photograph and writes a problem briefing:
        - Azure Computer Vision analyzes image (pothole).
        - Azure AI Language analyzes written briefing (pothole + water/school context).
        - Combined interpretation synthesized and persisted.
        """
        # 1. Create incident with briefing
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={
                "title": "Road hazard near school",
                "description": "Large pothole outside the primary school fills with water during rain.",
                "issue_type": "road_damage",
            },
        )
        assert create_res.status_code == 201
        incident_id = create_res.json()["id"]

        # 2. Upload evidence with briefing description
        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 150
        files = {"file": ("pothole.jpg", io.BytesIO(file_bytes), "image/jpeg")}
        data = {
            "description": "Large pothole outside the primary school fills with water during rain.",
            "evidence_type": "image",
        }

        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta",
                (),
                {
                    "storage_key": f"incidents/{incident_id}/evidence/pothole.jpg",
                    "file_size_bytes": len(file_bytes),
                },
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files=files,
                data=data,
            )
            assert upload_res.status_code == 201
            evidence_id = upload_res.json()["id"]

        # 3. Trigger AI perception analysis
        mock_vision_result = AIAnalysisResult(
            civic_issue_category=IssueType.POTHOLE,
            confidence=0.92,
            severity_assessment=SeverityLevel.HIGH,
            safety_risk_detected=False,
            ambiguity_flag=False,
            ambiguity_reason=None,
            extracted_attributes={"provider": "azure_computer_vision", "tags": ["pothole", "asphalt"]},
            explanation="Azure Computer Vision observed large road-surface pothole in asphalt lane.",
            visual_perception=VisualPerceptionResult(
                issue_category=IssueType.POTHOLE,
                description="large road-surface pothole in asphalt lane",
                severity=SeverityLevel.HIGH,
                confidence=0.92,
                tags=["pothole", "asphalt"],
            ),
        )

        mock_language_result = LanguagePerceptionResult(
            status="success",
            detected_category=IssueType.POTHOLE,
            issue_terms=["pothole", "water", "rain"],
            key_phrases=["large pothole", "primary school", "water"],
            impact_phrases=["school", "rain"],
            safety_risk_detected=False,
            confidence=0.85,
            summary="Citizen briefing describes pothole: 'Large pothole outside the primary school fills with water during rain.'",
            provider="azure_ai_language",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_vision, \
             patch("app.services.ai.language.AzureLanguageProvider.analyze_text", new_callable=AsyncMock) as mock_lang:

            mock_signed_url.return_value = "https://supabase.mock/signed/pothole.jpg"
            mock_vision.return_value = mock_vision_result
            mock_lang.return_value = mock_language_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            # Verify combined multi-modal perception
            assert ai_data["civic_issue_category"] == IssueType.POTHOLE.value
            assert ai_data["confidence"] == pytest.approx(0.92, rel=1e-2)
            assert ai_data["visual_perception"]["issue_category"] == IssueType.POTHOLE.value
            assert ai_data["language_perception"]["detected_category"] == IssueType.POTHOLE.value
            assert "pothole" in ai_data["language_perception"]["issue_terms"]
            assert "Citizen briefing:" in ai_data["combined_interpretation"]
            assert mock_lang.called

    async def test_image_only_skips_language_analysis(
        self, async_client: AsyncClient
    ):
        """
        When evidence has no written description, Azure AI Language is not invoked.
        Vision perception runs normally.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Photo report without text", "issue_type": "water_leak"},
        )
        incident_id = create_res.json()["id"]

        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        files = {"file": ("pipe.jpg", io.BytesIO(file_bytes), "image/jpeg")}
        # Empty description
        data = {"evidence_type": "image", "description": ""}

        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta",
                (),
                {
                    "storage_key": f"incidents/{incident_id}/evidence/pipe.jpg",
                    "file_size_bytes": len(file_bytes),
                },
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files=files,
                data=data,
            )
            evidence_id = upload_res.json()["id"]

        mock_vision_result = AIAnalysisResult(
            civic_issue_category=IssueType.WATER_LEAK,
            confidence=0.88,
            severity_assessment=SeverityLevel.MEDIUM,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Azure Computer Vision observed burst water pipeline.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_vision, \
             patch("app.services.ai.language.AzureLanguageProvider.analyze_text", new_callable=AsyncMock) as mock_lang:

            mock_signed_url.return_value = "https://supabase.mock/signed/pipe.jpg"
            mock_vision.return_value = mock_vision_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            assert ai_data["civic_issue_category"] == IssueType.WATER_LEAK.value
            assert ai_data["language_perception"] is None
            assert not mock_lang.called

    async def test_language_failure_preserves_vision_result(
        self, async_client: AsyncClient
    ):
        """
        If Azure AI Language experiences an operational failure, the visual perception
        is preserved, evidence transitions to PROCESSED, and the workflow continues.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Streetlight failure", "issue_type": "broken_streetlight"},
        )
        incident_id = create_res.json()["id"]

        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta",
                (),
                {"storage_key": f"incidents/{incident_id}/evidence/light.jpg", "file_size_bytes": len(file_bytes)},
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("light.jpg", io.BytesIO(file_bytes), "image/jpeg")},
                data={"description": "Light pole completely dark at night."},
            )
            evidence_id = upload_res.json()["id"]

        mock_vision_result = AIAnalysisResult(
            civic_issue_category=IssueType.BROKEN_STREETLIGHT,
            confidence=0.90,
            severity_assessment=SeverityLevel.LOW,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Azure Computer Vision observed dark lamp post fixture.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_vision, \
             patch("app.services.ai.language.AzureLanguageProvider.analyze_text", side_effect=AzureLanguageOperationalError("Language endpoint down")):

            mock_signed_url.return_value = "https://supabase.mock/signed/light.jpg"
            mock_vision.return_value = mock_vision_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            assert ai_data["civic_issue_category"] == IssueType.BROKEN_STREETLIGHT.value
            assert ai_data["language_perception"]["status"] == "unavailable"

        # Check DB persistence
        list_res = await async_client.get(f"/api/v1/incidents/{incident_id}/evidence")
        target_ev = next(e for e in list_res.json() if e["id"] == evidence_id)
        assert target_ev["status"] == EvidenceStatus.PROCESSED.value
        assert target_ev["ai_category"] == "broken_streetlight"

    async def test_vision_and_language_conflict_flags_ambiguity_without_overriding_vision(
        self, async_client: AsyncClient
    ):
        """
        If Vision identifies POTHOLE but citizen text describes ILLEGAL_DUMPING:
        - Vision category is NOT overridden.
        - Ambiguity flag is set to True.
        - Detailed conflict reason is preserved.
        """
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Conflicting report", "issue_type": "other"},
        )
        incident_id = create_res.json()["id"]

        file_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta",
                (),
                {"storage_key": f"incidents/{incident_id}/evidence/conflict.jpg", "file_size_bytes": len(file_bytes)},
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("conflict.jpg", io.BytesIO(file_bytes), "image/jpeg")},
                data={"description": "Large garbage heap and open waste dumping next to residential gate."},
            )
            evidence_id = upload_res.json()["id"]

        # Vision sees Pothole
        mock_vision_result = AIAnalysisResult(
            civic_issue_category=IssueType.POTHOLE,
            confidence=0.89,
            severity_assessment=SeverityLevel.MEDIUM,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Azure Computer Vision observed asphalt pothole.",
        )

        # Language extracts Illegal Dumping
        mock_language_result = LanguagePerceptionResult(
            status="success",
            detected_category=IssueType.ILLEGAL_DUMPING,
            issue_terms=["garbage", "dumping", "waste"],
            key_phrases=["large garbage heap", "open waste dumping"],
            confidence=0.90,
            summary="Citizen briefing describes illegal dumping.",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_vision, \
             patch("app.services.ai.language.AzureLanguageProvider.analyze_text", new_callable=AsyncMock) as mock_lang:

            mock_signed_url.return_value = "https://supabase.mock/signed/conflict.jpg"
            mock_vision.return_value = mock_vision_result
            mock_lang.return_value = mock_language_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            ai_data = analyze_res.json()

            # Vision category is NOT overridden by language
            assert ai_data["civic_issue_category"] == IssueType.POTHOLE.value
            # Ambiguity flag raised due to conflict
            assert ai_data["ambiguity_flag"] is True
            assert "Perception conflict" in ai_data["ambiguity_reason"]
            assert "pothole" in ai_data["ambiguity_reason"].lower()
            assert "illegal dumping" in ai_data["ambiguity_reason"].lower()
            assert "Flagged for review" in ai_data["combined_interpretation"]

    async def test_end_to_end_voice_transcription_into_multi_modal_perception(
        self, async_client: AsyncClient
    ):
        """
        Citizen records voice briefing -> speech transcribed -> incident submitted with text -> multi-modal perception.
        """
        # 1. Citizen records voice and transcribes
        mock_stt = SpeechTranscriptionResponse(
            text="Exposed high voltage wire sparking on street pole.",
            confidence=0.95,
            language="en-US",
        )

        with patch("app.services.ai.speech.AzureSpeechProvider.transcribe_audio", new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = mock_stt
            stt_res = await async_client.post(
                "/api/v1/ai/transcribe",
                files={"file": ("voice.webm", io.BytesIO(b"audio"), "audio/webm")},
                data={"language": "en-US"},
            )
            assert stt_res.status_code == 200
            transcribed_text = stt_res.json()["text"]

        # 2. Citizen creates incident using transcribed text
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={
                "title": "Sparking wire",
                "description": transcribed_text,
                "issue_type": "other",
            },
        )
        assert create_res.status_code == 201
        incident_id = create_res.json()["id"]

        # 3. Upload evidence and analyze
        with patch("app.services.storage_service.StorageService.upload_object") as mock_upload:
            mock_upload.return_value = type(
                "StorageMeta",
                (),
                {"storage_key": f"incidents/{incident_id}/evidence/spark.jpg", "file_size_bytes": 100},
            )()
            upload_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/upload",
                files={"file": ("spark.jpg", io.BytesIO(b"image-bytes"), "image/jpeg")},
                data={"description": transcribed_text},
            )
            evidence_id = upload_res.json()["id"]

        mock_vision_result = AIAnalysisResult(
            civic_issue_category=None,
            confidence=0.60,
            severity_assessment=SeverityLevel.HIGH,
            safety_risk_detected=True,
            ambiguity_flag=False,
            explanation="Azure Computer Vision observed electrical utility pole.",
        )

        mock_language_result = LanguagePerceptionResult(
            status="success",
            detected_category=None,
            issue_terms=["wire", "sparking", "voltage"],
            impact_phrases=["high voltage", "sparking"],
            safety_risk_detected=True,
            confidence=0.88,
            summary="Citizen briefing: 'Exposed high voltage wire sparking on street pole.'",
        )

        with patch("app.services.storage_service.StorageService.create_signed_url", new_callable=AsyncMock) as mock_signed_url, \
             patch("app.services.ai.azure.AzureVisionProvider.analyze_evidence", new_callable=AsyncMock) as mock_vision, \
             patch("app.services.ai.language.AzureLanguageProvider.analyze_text", new_callable=AsyncMock) as mock_lang:

            mock_signed_url.return_value = "https://supabase.mock/signed/spark.jpg"
            mock_vision.return_value = mock_vision_result
            mock_lang.return_value = mock_language_result

            analyze_res = await async_client.post(
                f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze"
            )
            assert analyze_res.status_code == 200
            data = analyze_res.json()
            assert data["safety_risk_detected"] is True
            assert data["language_perception"]["safety_risk_detected"] is True
            assert "sparking" in data["combined_interpretation"]

"""
Unit tests for AI Perception layer (Gemini).
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import APIError
from pydantic import ValidationError

from app.core.errors import CivicTraceError
from app.models.enums import EvidenceStatus, IssueType, SeverityLevel
from app.models.evidence import Evidence
from app.schemas.ai import AIAnalysisResult
from app.services.ai.gemini import GeminiAIProvider
from app.services.ai.service import AIService


@pytest.fixture
def mock_gemini_client():
    with patch("app.services.ai.gemini.genai.Client") as mock_client:
        client_instance = mock_client.return_value
        yield client_instance


@pytest.fixture
def ai_provider(mock_gemini_client):
    return GeminiAIProvider()


class MockGenerateContentResponse:
    def __init__(self, text):
        self.text = text


@pytest.mark.asyncio
class TestGeminiAIProvider:
    async def test_text_based_analysis_valid(self, ai_provider, mock_gemini_client):
        # 3. Text-based analysis
        # 1. Valid AI response
        # 4. Valid structured output
        # 16. Cache miss
        mock_response = {
            "civic_issue_category": "pothole",
            "confidence": 0.95,
            "severity_assessment": "medium",
            "safety_risk_detected": True,
            "ambiguity_flag": False,
            "extracted_attributes": {"size": "large"},
            "explanation": "Clear pothole description."
        }
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps(mock_response)
        )

        result = await ai_provider.analyze_evidence(
            description="Huge pothole on Main St", media_urls=[]
        )
        assert result.civic_issue_category == IssueType.POTHOLE
        assert result.confidence == 0.95
        assert result.safety_risk_detected is True

    async def test_image_based_analysis(self, ai_provider, mock_gemini_client):
        # 2. Image-based analysis
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": "graffiti",
                "confidence": 0.8,
                "safety_risk_detected": False,
                "ambiguity_flag": False,
                "explanation": "Graffiti on wall",
                "extracted_attributes": {}
            })
        )

        result = await ai_provider.analyze_evidence(
            description=None, media_urls=["s3://bucket/image.jpg"]
        )
        assert result.civic_issue_category == IssueType.GRAFFITI

    async def test_cache_hit(self, ai_provider, mock_gemini_client):
        # 15. Cache hit
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": "pothole",
                "confidence": 0.9,
                "safety_risk_detected": False,
                "ambiguity_flag": False,
                "explanation": "...",
                "extracted_attributes": {}
            })
        )
        # First call caches
        res1 = await ai_provider.analyze_evidence("Cache test", [])
        # Change mock to ensure it's not called
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse("{}")

        # Second call should hit cache
        res2 = await ai_provider.analyze_evidence("Cache test", [])
        assert res1 == res2
        assert mock_gemini_client.models.generate_content.call_count == 1

    async def test_malformed_json(self, ai_provider, mock_gemini_client):
        # 5. Malformed JSON
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            "```json\n{ invalid json\n```"
        )
        with pytest.raises(CivicTraceError) as exc:
            await ai_provider.analyze_evidence("Bad JSON", [])
        assert exc.value.error_code == "SERVICE_UNAVAILABLE"

    async def test_missing_required_field(self, ai_provider, mock_gemini_client):
        # 6. Missing required field (explanation is required)
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({"confidence": 0.9})
        )
        with pytest.raises(CivicTraceError) as exc:
            await ai_provider.analyze_evidence("Missing fields", [])
        assert exc.value.error_code == "AI_VALIDATION_ERROR"

    async def test_invalid_enum(self, ai_provider, mock_gemini_client):
        # 7. Invalid enum
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": "alien_invasion",
                "confidence": 0.9,
                "explanation": "..."
            })
        )
        with pytest.raises(CivicTraceError) as exc:
            await ai_provider.analyze_evidence("Invalid enum", [])
        assert exc.value.error_code == "AI_VALIDATION_ERROR"

    async def test_invalid_confidence(self, ai_provider, mock_gemini_client):
        # 8. Invalid confidence
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": "pothole",
                "confidence": 2.5, # > 1.0
                "explanation": "..."
            })
        )
        with pytest.raises(CivicTraceError) as exc:
            await ai_provider.analyze_evidence("Invalid confidence", [])
        assert exc.value.error_code == "AI_VALIDATION_ERROR"

    async def test_low_confidence_and_ambiguity(self, ai_provider, mock_gemini_client):
        # 9. Low confidence
        # 10. Ambiguous evidence
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": None,
                "confidence": 0.1,
                "ambiguity_flag": True,
                "ambiguity_reason": "Too blurry to identify issue.",
                "explanation": "Low confidence due to image quality."
            })
        )
        res = await ai_provider.analyze_evidence("Blurry pic", [])
        assert res.confidence == 0.1
        assert res.ambiguity_flag is True
        assert res.civic_issue_category is None

    async def test_empty_evidence(self, ai_provider, mock_gemini_client):
        # 11. Empty evidence
        mock_gemini_client.models.generate_content.return_value = MockGenerateContentResponse(
            json.dumps({
                "civic_issue_category": None,
                "confidence": 0.0,
                "ambiguity_flag": True,
                "ambiguity_reason": "No evidence provided.",
                "explanation": "Empty input."
            })
        )
        res = await ai_provider.analyze_evidence(None, [])
        assert res.confidence == 0.0
        assert res.ambiguity_flag is True

    async def test_gemini_failures(self, ai_provider, mock_gemini_client):
        # 12. Timeout
        # 13. Rate limit
        # 14. Unavailable
        # 8. Failure handling
        mock_gemini_client.models.generate_content.side_effect = Exception("Rate limit exceeded")
        with pytest.raises(CivicTraceError) as exc:
            await ai_provider.analyze_evidence("Rate limit", [])
        assert exc.value.error_code == "SERVICE_UNAVAILABLE"
        assert "Rate limit exceeded" in str(exc.value)

@pytest.mark.asyncio
class TestAIService:
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock(spec=GeminiAIProvider)
        return provider

    async def test_persistence_of_validated_result(self, db_session, mock_provider):
        # 17. Persistence of validated result
        from app.models.incident import Incident

        inc = Incident(
            reference_number="INC-123", status="draft", evidence_count=1
        )
        db_session.add(inc)
        await db_session.flush()

        ev = Evidence(
            incident_id=inc.id,
            evidence_type="image",
            status=EvidenceStatus.PENDING,
            description="Test persistence"
        )
        db_session.add(ev)
        await db_session.flush()

        mock_provider.analyze_evidence.return_value = AIAnalysisResult(
            civic_issue_category=IssueType.POTHOLE,
            confidence=0.99,
            severity_assessment=SeverityLevel.HIGH,
            safety_risk_detected=True,
            ambiguity_flag=False,
            explanation="Test"
        )

        ai_service = AIService(db_session, provider=mock_provider)
        await ai_service.process_evidence(ev.id)

        # Refresh from DB to verify persistence
        await db_session.refresh(ev)

        assert ev.status == EvidenceStatus.PROCESSED
        assert ev.ai_category == "pothole"
        assert ev.ai_confidence == 0.99
        assert ev.ai_severity_raw == "high"
        assert ev.ai_safety_risk is True
        assert ev.ai_ambiguity_flag is False
        assert ev.ai_perception_payload is not None

    async def test_failure_reverts_to_failed_status(self, db_session, mock_provider):
        from app.models.incident import Incident

        inc = Incident(
            reference_number="INC-124", status="draft", evidence_count=1
        )
        db_session.add(inc)
        await db_session.flush()

        ev = Evidence(
            incident_id=inc.id,
            evidence_type="text",
            status=EvidenceStatus.PENDING,
        )
        db_session.add(ev)
        await db_session.flush()

        # Provider raises an error
        mock_provider.analyze_evidence.side_effect = CivicTraceError("API down")

        ai_service = AIService(db_session, provider=mock_provider)

        with pytest.raises(CivicTraceError):
            await ai_service.process_evidence(ev.id)

        await db_session.refresh(ev)
        assert ev.status == EvidenceStatus.FAILED

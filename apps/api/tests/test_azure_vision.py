"""
test_azure_vision.py
====================
Mocked unit tests for Azure Computer Vision provider and AIService fallback architecture.

Covers:
1. Azure provider success
2. Azure response parsing
3. Azure malformed response
4. Azure timeout
5. Azure authentication failure
6. Azure operational failure -> Gemini fallback
7. Azure valid low-confidence result -> NO fallback
8. Azure ambiguity -> NO fallback
9. Both providers fail
10. Structured CivicTrace output validation
11. Confidence bounds
12. Secret/config protection
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import CivicTraceError, ServiceUnavailableError
from app.models.enums import EvidenceStatus, IssueType, SeverityLevel
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.schemas.ai import AIAnalysisResult
from app.services.ai.azure import AzureOperationalError, AzureVisionProvider
from app.services.ai.base import AIProvider
from app.services.ai.service import AIService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def azure_provider():
    return AzureVisionProvider(
        endpoint="https://test-vision.cognitiveservices.azure.com/",
        key="mock-secret-key-12345",
        timeout=5.0,
    )


def build_azure_response(
    tags: list[dict[str, float | str]] | None = None,
    caption: str | None = None,
    caption_confidence: float = 0.85,
    objects: list[str] | None = None,
) -> dict:
    return {
        "tags": tags or [{"name": "road", "confidence": 0.95}, {"name": "pothole", "confidence": 0.91}],
        "description": {
            "tags": [t["name"] for t in (tags or [])],
            "captions": [{"text": caption or "a deep pothole in an asphalt road", "confidence": caption_confidence}],
        },
        "categories": [{"name": "outdoor_", "score": 0.9}],
        "objects": [{"object": obj, "confidence": 0.88} for obj in (objects or [])],
        "requestId": "test-req-id-1234",
    }


# ===========================================================================
# 1. Azure provider success
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_provider_success(azure_provider):
    """1. Azure provider successfully analyzes image and identifies issue category."""
    mock_body = build_azure_response(
        tags=[{"name": "pothole", "confidence": 0.92}, {"name": "asphalt", "confidence": 0.88}],
        caption="a large pothole on the roadway",
        caption_confidence=0.90,
    )
    mock_resp = httpx.Response(status_code=200, json=mock_body)

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await azure_provider.analyze_evidence(
            description="Road crater",
            media_urls=["https://supabase.local/evidence/photo.jpg"],
        )

    assert result.civic_issue_category == IssueType.POTHOLE
    assert result.confidence == pytest.approx(0.92, rel=1e-2)
    assert result.safety_risk_detected is False
    assert result.ambiguity_flag is False
    assert "pothole" in result.explanation.lower()
    assert result.extracted_attributes["provider"] == "azure_computer_vision"


# ===========================================================================
# 2. Azure response parsing
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_response_parsing(azure_provider):
    """2. Raw Azure response fields (tags, captions, objects) are correctly parsed."""
    mock_body = build_azure_response(
        tags=[
            {"name": "flooding", "confidence": 0.89},
            {"name": "water", "confidence": 0.95},
            {"name": "hazard", "confidence": 0.75},
        ],
        caption="water flooding a residential road",
        caption_confidence=0.87,
        objects=["puddle", "car"],
    )
    mock_resp = httpx.Response(status_code=200, json=mock_body)

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await azure_provider.analyze_evidence(
            description=None,
            media_urls=["https://supabase.local/evidence/flood.jpg"],
        )

    assert result.civic_issue_category == IssueType.FLOODING
    assert result.safety_risk_detected is True  # 'hazard' tag triggers safety risk
    assert result.severity_assessment == SeverityLevel.HIGH
    assert "flooding" in result.extracted_attributes["tags"]
    assert result.extracted_attributes["detected_objects"] == ["puddle", "car"]
    assert result.extracted_attributes["caption"] == "water flooding a residential road"


# ===========================================================================
# 3. Azure malformed response
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_malformed_response(azure_provider):
    """3. Non-JSON response from Azure raises an operational error."""
    mock_resp = httpx.Response(status_code=200, content=b"<html>502 Bad Gateway</html>")

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(AzureOperationalError) as exc_info:
            await azure_provider.analyze_evidence(
                description=None,
                media_urls=["https://supabase.local/evidence/test.jpg"],
            )

    assert "malformed JSON" in str(exc_info.value)


# ===========================================================================
# 4. Azure timeout
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_timeout(azure_provider):
    """4. HTTP timeout communicating with Azure raises AzureOperationalError."""
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out after 5s")
        with pytest.raises(AzureOperationalError) as exc_info:
            await azure_provider.analyze_evidence(
                description="Test",
                media_urls=["https://supabase.local/evidence/test.jpg"],
            )

    assert "timed out" in str(exc_info.value).lower()


# ===========================================================================
# 5. Azure authentication failure
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_authentication_failure(azure_provider):
    """5. HTTP 401/403 response raises AzureOperationalError without leaking key."""
    mock_resp = httpx.Response(status_code=401, json={"error": {"code": "401", "message": "Access denied"}})

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(AzureOperationalError) as exc_info:
            await azure_provider.analyze_evidence(
                description="Auth test",
                media_urls=["https://supabase.local/evidence/test.jpg"],
            )

    assert "authentication failed" in str(exc_info.value).lower()
    # Ensure key is not leaked in error message
    assert "mock-secret-key" not in str(exc_info.value)


# ===========================================================================
# 6. Azure operational failure -> Gemini fallback
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_operational_failure_triggers_fallback(db_session):
    """6. Operational failure on Azure triggers automated fallback to Gemini."""
    inc = Incident(reference_number="INC-FB-001", status="draft", evidence_count=1)
    db_session.add(inc)
    await db_session.flush()

    ev = Evidence(
        incident_id=inc.id,
        evidence_type="image",
        status=EvidenceStatus.PENDING,
        description="Pothole near market",
    )
    db_session.add(ev)
    await db_session.flush()

    # Mock Azure failing operationally (e.g. 503 Service Unavailable)
    mock_azure = MagicMock(spec=AIProvider)
    mock_azure.analyze_evidence = AsyncMock(
        side_effect=AzureOperationalError("Azure service unavailable (status 503).")
    )

    # Mock Gemini succeeding
    mock_gemini = MagicMock(spec=AIProvider)
    mock_gemini.analyze_evidence = AsyncMock(
        return_value=AIAnalysisResult(
            civic_issue_category=IssueType.POTHOLE,
            confidence=0.88,
            severity_assessment=SeverityLevel.MEDIUM,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Gemini fallback resolved pothole.",
        )
    )

    service = AIService(
        session=db_session,
        provider=mock_azure,
        fallback_provider=mock_gemini,
    )
    result = await service.process_evidence(ev.id)

    # Verify fallback was invoked
    assert mock_azure.analyze_evidence.call_count == 1
    assert mock_gemini.analyze_evidence.call_count == 1
    assert result.civic_issue_category == IssueType.POTHOLE
    assert result.confidence == 0.88

    # Verify DB record updated
    await db_session.refresh(ev)
    assert ev.status == EvidenceStatus.PROCESSED
    assert ev.ai_category == "pothole"


# ===========================================================================
# 7. Azure valid low-confidence result -> NO fallback
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_low_confidence_does_not_trigger_fallback(db_session):
    """7. Valid Azure response with low confidence must NOT trigger fallback."""
    inc = Incident(reference_number="INC-LOW-001", status="draft", evidence_count=1)
    db_session.add(inc)
    await db_session.flush()

    ev = Evidence(
        incident_id=inc.id,
        evidence_type="image",
        status=EvidenceStatus.PENDING,
        description="Blurry surface",
    )
    db_session.add(ev)
    await db_session.flush()

    # Azure returns valid but low confidence
    mock_azure = MagicMock(spec=AIProvider)
    mock_azure.analyze_evidence = AsyncMock(
        return_value=AIAnalysisResult(
            civic_issue_category=IssueType.ROAD_DAMAGE,
            confidence=0.35,
            severity_assessment=SeverityLevel.LOW,
            safety_risk_detected=False,
            ambiguity_flag=True,
            ambiguity_reason="Low visual perception confidence (0.35).",
            explanation="Azure detected slight road cracks with low confidence.",
        )
    )

    mock_gemini = MagicMock(spec=AIProvider)
    mock_gemini.analyze_evidence = AsyncMock()

    service = AIService(
        session=db_session,
        provider=mock_azure,
        fallback_provider=mock_gemini,
    )
    result = await service.process_evidence(ev.id)

    # Gemini must NOT have been called
    assert mock_gemini.analyze_evidence.call_count == 0
    assert result.confidence == 0.35
    assert result.ambiguity_flag is True

    await db_session.refresh(ev)
    assert ev.status == EvidenceStatus.PROCESSED
    assert ev.ai_confidence == 0.35
    assert ev.ai_ambiguity_flag is True


# ===========================================================================
# 8. Azure ambiguity -> NO fallback
# ===========================================================================

@pytest.mark.asyncio
async def test_azure_ambiguity_does_not_trigger_fallback(db_session):
    """8. Ambiguous Azure response (no matched category) must NOT trigger fallback."""
    inc = Incident(reference_number="INC-AMB-001", status="draft", evidence_count=1)
    db_session.add(inc)
    await db_session.flush()

    ev = Evidence(
        incident_id=inc.id,
        evidence_type="image",
        status=EvidenceStatus.PENDING,
        description="Unclear photo",
    )
    db_session.add(ev)
    await db_session.flush()

    mock_azure = MagicMock(spec=AIProvider)
    mock_azure.analyze_evidence = AsyncMock(
        return_value=AIAnalysisResult(
            civic_issue_category=None,
            confidence=0.55,
            severity_assessment=None,
            safety_risk_detected=False,
            ambiguity_flag=True,
            ambiguity_reason="Visual evidence lacks recognizable civic issue features.",
            explanation="Azure Computer Vision detected: 'a group of people posing for a photo'.",
        )
    )

    mock_gemini = MagicMock(spec=AIProvider)
    mock_gemini.analyze_evidence = AsyncMock()

    service = AIService(
        session=db_session,
        provider=mock_azure,
        fallback_provider=mock_gemini,
    )
    result = await service.process_evidence(ev.id)

    # Gemini was NOT called
    assert mock_gemini.analyze_evidence.call_count == 0
    assert result.civic_issue_category is None
    assert result.ambiguity_flag is True

    await db_session.refresh(ev)
    assert ev.status == EvidenceStatus.PROCESSED
    assert ev.ai_category is None
    assert ev.ai_ambiguity_flag is True


# ===========================================================================
# 9. Both providers fail
# ===========================================================================

@pytest.mark.asyncio
async def test_both_providers_fail(db_session):
    """9. Controlled failure when both primary and fallback fail; DB status moves to FAILED."""
    inc = Incident(reference_number="INC-BOTH-FAIL", status="draft", evidence_count=1)
    db_session.add(inc)
    await db_session.flush()

    ev = Evidence(
        incident_id=inc.id,
        evidence_type="image",
        status=EvidenceStatus.PENDING,
    )
    db_session.add(ev)
    await db_session.flush()

    mock_azure = MagicMock(spec=AIProvider)
    mock_azure.analyze_evidence = AsyncMock(side_effect=AzureOperationalError("Azure down"))

    mock_gemini = MagicMock(spec=AIProvider)
    mock_gemini.analyze_evidence = AsyncMock(side_effect=ServiceUnavailableError("Gemini down"))

    service = AIService(
        session=db_session,
        provider=mock_azure,
        fallback_provider=mock_gemini,
    )

    with pytest.raises(ServiceUnavailableError):
        await service.process_evidence(ev.id)

    await db_session.refresh(ev)
    assert ev.status == EvidenceStatus.FAILED
    # AI fields are not corrupted
    assert ev.ai_category is None
    assert ev.ai_confidence is None


# ===========================================================================
# 10. Structured CivicTrace output validation
# ===========================================================================

def test_structured_output_validation():
    """10. AIAnalysisResult validates data types, enums, and required fields."""
    # Valid output
    res = AIAnalysisResult(
        civic_issue_category=IssueType.BROKEN_STREETLIGHT,
        confidence=0.89,
        severity_assessment=SeverityLevel.LOW,
        safety_risk_detected=False,
        ambiguity_flag=False,
        explanation="Dark streetlight detected.",
    )
    assert res.civic_issue_category == IssueType.BROKEN_STREETLIGHT

    # Missing explanation should fail validation
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            confidence=0.8,
            safety_risk_detected=False,
            ambiguity_flag=False,
        )


# ===========================================================================
# 11. Confidence bounds
# ===========================================================================

def test_confidence_bounds_enforcement():
    """11. Confidence must be strictly between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            confidence=-0.1,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Invalid negative confidence",
        )

    with pytest.raises(ValidationError):
        AIAnalysisResult(
            confidence=1.1,
            safety_risk_detected=False,
            ambiguity_flag=False,
            explanation="Invalid >1.0 confidence",
        )


# ===========================================================================
# 12. Secret and configuration protection
# ===========================================================================

def test_secret_protection(azure_provider):
    """12. Subscription keys must not be exposed in repr, str, or error messages."""
    provider_str = str(azure_provider)
    provider_repr = repr(azure_provider)

    # Provider string representations must not expose secret key
    assert "mock-secret-key" not in provider_str
    assert "mock-secret-key" not in provider_repr

    # Operational errors must not leak secrets
    err = AzureOperationalError("Authentication failed at endpoint https://test.cognitiveservices.azure.com/")
    assert "mock-secret-key" not in str(err)

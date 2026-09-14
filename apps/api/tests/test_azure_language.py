"""
test_azure_language.py
======================
Unit tests for AzureLanguageProvider and normalization layer.
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.models.enums import IssueType
from app.services.ai.language import (
    AzureLanguageOperationalError,
    AzureLanguageProvider,
)
from app.services.ai.normalization import normalize_language_perception


@pytest.mark.asyncio
class TestAzureLanguageProvider:
    async def test_empty_or_whitespace_text_skipped(self):
        provider = AzureLanguageProvider(endpoint="https://mock.cognitiveservices.azure.com", key="mock-key")

        res1 = await provider.analyze_text(None)
        assert res1.status == "skipped"
        assert "No written briefing" in res1.summary
        assert res1.confidence is None

        res2 = await provider.analyze_text("   \n\t  ")
        assert res2.status == "skipped"
        assert "No written briefing" in res2.summary
        assert res2.confidence is None

    async def test_unconfigured_credentials_raises_operational_error(self):
        provider = AzureLanguageProvider(endpoint="", key="")
        with pytest.raises(AzureLanguageOperationalError, match="not configured"):
            await provider.analyze_text("Large pothole on the road")

    async def test_successful_text_analysis_keyphrase_extraction(self):
        provider = AzureLanguageProvider(
            endpoint="https://mock.cognitiveservices.azure.com", key="mock-key"
        )

        mock_raw_response = {
            "kind": "KeyPhraseExtractionResults",
            "results": {
                "documents": [
                    {
                        "id": "1",
                        "keyPhrases": [
                            "large pothole",
                            "school",
                            "water",
                            "rains",
                        ],
                        "warnings": [],
                    }
                ],
                "errors": [],
                "modelVersion": "2023-04-01",
            },
        }

        mock_http_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: mock_raw_response,
                "text": "OK",
            },
        )()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response

            text = "There is a large pothole outside the school. It fills with water whenever it rains."
            result = await provider.analyze_text(text, language="en")

            # Pure provider output verification (no synthetic confidence, no domain category)
            assert result.status == "success"
            assert "large pothole" in result.key_phrases
            assert "school" in result.key_phrases
            assert result.confidence is None
            assert result.provider == "azure_ai_language"

    async def test_normalization_layer_category_and_hazard_mapping(self):
        # Normalize pothole problem briefing
        provider = AzureLanguageProvider(
            endpoint="https://mock.cognitiveservices.azure.com", key="mock-key"
        )
        mock_raw_response = {
            "results": {
                "documents": [
                    {
                        "id": "1",
                        "keyPhrases": ["large pothole", "school", "water"],
                    }
                ]
            }
        }
        mock_http_response = type(
            "MockResponse",
            (),
            {"status_code": 200, "json": lambda self: mock_raw_response, "text": "OK"},
        )()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response
            text = "There is a large pothole outside the school. It fills with water whenever it rains."
            raw_res = await provider.analyze_text(text)
            norm_res = normalize_language_perception(raw_res, text)

            assert norm_res.detected_category == IssueType.POTHOLE
            assert "pothole" in norm_res.issue_terms
            assert "school" in norm_res.impact_phrases or "rain" in norm_res.impact_phrases
            assert norm_res.safety_risk_detected is False
            assert norm_res.confidence is None

    async def test_normalization_layer_safety_hazard_detection(self):
        provider = AzureLanguageProvider(
            endpoint="https://mock.cognitiveservices.azure.com", key="mock-key"
        )

        mock_raw_response = {
            "results": {
                "documents": [
                    {
                        "id": "1",
                        "keyPhrases": ["exposed wire", "sparking transformer", "danger"],
                    }
                ]
            }
        }

        mock_http_response = type(
            "MockResponse",
            (),
            {"status_code": 200, "json": lambda self: mock_raw_response, "text": "OK"},
        )()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response

            text = "Live wire sparking near pedestrian crossing. Immediate danger and electric shock hazard!"
            raw_res = await provider.analyze_text(text)
            norm_res = normalize_language_perception(raw_res, text)

            assert norm_res.status == "success"
            assert norm_res.safety_risk_detected is True
            assert norm_res.detected_category == IssueType.OTHER

    async def test_azure_language_http_errors_raise_operational_error(self):
        provider = AzureLanguageProvider(
            endpoint="https://mock.cognitiveservices.azure.com", key="mock-key"
        )

        # 401 Auth error
        mock_401 = type("MockResponse", (), {"status_code": 401, "text": "Access denied"})()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_401
            with pytest.raises(AzureLanguageOperationalError, match="authentication failed"):
                await provider.analyze_text("Broken streetlight")

        # 500 Server error
        mock_500 = type("MockResponse", (), {"status_code": 500, "text": "Server Error"})()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_500
            with pytest.raises(AzureLanguageOperationalError, match="unavailable"):
                await provider.analyze_text("Garbage overflowing")

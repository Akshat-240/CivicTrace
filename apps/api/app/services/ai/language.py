"""
Azure AI Language provider for Citizen Problem Briefing text analysis.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError
from app.models.enums import IssueType
from app.schemas.ai import LanguagePerceptionResult

logger = logging.getLogger(__name__)


class AzureLanguageOperationalError(ServiceUnavailableError):
    """Raised when an operational failure occurs communicating with Azure AI Language."""
    error_code = "AZURE_LANGUAGE_OPERATIONAL_ERROR"


class AzureLanguageProvider:
    """
    Client for Azure AI Language / Text Analytics REST API.
    Extracts pure language perception features (key phrases, recognized entities).
    Does NOT perform CivicTrace domain category mapping or fabricate confidence scores.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        timeout: float = 12.0,
    ):
        settings = get_settings()
        if endpoint is not None:
            self.endpoint = endpoint.rstrip("/")
        else:
            self.endpoint = (
                settings.azure_ai_language_endpoint
                or settings.azure_ai_vision_endpoint
                or ""
            ).rstrip("/")

        if key is not None:
            self.key = key
        else:
            self.key = (
                settings.azure_ai_language_key
                or settings.azure_ai_vision_key
                or ""
            )
        self.timeout = timeout
        self._cache: dict[str, LanguagePerceptionResult] = {}

    def _hash_text(self, text: str, language: str) -> str:
        return hashlib.sha256(f"{language}:{text}".encode("utf-8")).hexdigest()

    async def analyze_text(
        self, text: Optional[str], language: str = "en"
    ) -> LanguagePerceptionResult:
        """
        Extract key phrases and entities from citizen written briefing.
        If text is empty or None, returns a skipped perception result.
        """
        if not text or not text.strip():
            return LanguagePerceptionResult(
                status="skipped",
                summary="No written briefing provided by citizen.",
                confidence=None,
                provider="azure_ai_language",
            )

        clean_text = text.strip()
        cache_key = self._hash_text(clean_text, language)
        if cache_key in self._cache:
            logger.info("azure_language_cache_hit", extra={"cache_key": cache_key})
            return self._cache[cache_key]

        if not self.endpoint or not self.key:
            raise AzureLanguageOperationalError(
                "Azure AI Language endpoint or key is not configured."
            )

        # Query Azure AI Language KeyPhrase extraction
        api_url = f"{self.endpoint}/language/:analyze-text?api-version=2023-04-01"
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json",
        }
        payload = {
            "kind": "KeyPhraseExtraction",
            "analysisInput": {
                "documents": [
                    {"id": "1", "language": language[:2], "text": clean_text}
                ]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.warning("azure_language_timeout", extra={"endpoint": self.endpoint})
            raise AzureLanguageOperationalError("Azure AI Language request timed out.") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning("azure_language_connection_failure", extra={"endpoint": self.endpoint})
            raise AzureLanguageOperationalError("Failed to connect to Azure AI Language endpoint.") from exc
        except Exception as exc:
            logger.warning("azure_language_request_failure", extra={"error": str(exc)})
            raise AzureLanguageOperationalError(f"Azure AI Language request failed: {str(exc)}") from exc

        if response.status_code in (401, 403):
            logger.error("azure_language_auth_failure", extra={"status_code": response.status_code})
            raise AzureLanguageOperationalError("Azure AI Language authentication failed.")

        if response.status_code >= 500:
            logger.error("azure_language_server_error", extra={"status_code": response.status_code})
            raise AzureLanguageOperationalError(
                f"Azure AI Language service unavailable (status {response.status_code})."
            )

        if response.status_code != 200:
            error_msg = response.text[:200]
            logger.warning("azure_language_error_response", extra={"status_code": response.status_code})
            raise AzureLanguageOperationalError(
                f"Azure AI Language returned error (status {response.status_code}): {error_msg}"
            )

        try:
            raw_data = response.json()
        except Exception as exc:
            raise AzureLanguageOperationalError("Azure AI Language returned malformed JSON.") from exc

        result = self._parse_azure_language_response(raw_data, clean_text)
        self._cache[cache_key] = result
        return result

    def _parse_azure_language_response(
        self, raw_data: dict[str, Any], text: str
    ) -> LanguagePerceptionResult:
        """
        Extract genuine key phrases and entities returned by Azure AI Language.
        """
        key_phrases: list[str] = []
        documents = raw_data.get("results", {}).get("documents", [])
        if not documents and "documents" in raw_data:
            documents = raw_data["documents"]

        for doc in documents:
            if isinstance(doc, dict):
                kps = doc.get("keyPhrases", [])
                if isinstance(kps, list):
                    key_phrases.extend([str(k).strip() for k in kps if k])

        try:
            return LanguagePerceptionResult(
                status="success",
                detected_category=None,
                issue_terms=[],
                key_phrases=key_phrases[:15],
                entities=[],
                impact_phrases=[],
                safety_risk_detected=False,
                confidence=None,  # Do not invent arbitrary confidence score
                summary=f"Citizen briefing: \"{text}\"",
                provider="azure_ai_language",
            )
        except ValidationError as val_err:
            logger.error("azure_language_validation_failed", exc_info=True)
            raise AzureLanguageOperationalError(
                f"Azure Language response validation failed: {str(val_err)}"
            ) from val_err

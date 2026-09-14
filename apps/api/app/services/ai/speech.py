"""
Azure AI Speech provider for Citizen Voice Briefing Speech-to-Text transcription.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError
from app.schemas.ai import SpeechTranscriptionResponse

logger = logging.getLogger(__name__)


class AzureSpeechOperationalError(ServiceUnavailableError):
    """Raised when an operational failure occurs communicating with Azure Speech service."""
    error_code = "AZURE_SPEECH_OPERATIONAL_ERROR"


class AzureSpeechProvider:
    """
    Transcribes spoken citizen problem briefings into text using Azure Cognitive Services Speech REST API.
    Audio recordings are processed in memory and never persisted permanently.
    """

    def __init__(
        self,
        key: Optional[str] = None,
        region: Optional[str] = None,
        timeout: float = 15.0,
    ):
        settings = get_settings()
        if key is not None:
            self.key = key
        else:
            self.key = settings.azure_ai_speech_key or settings.azure_ai_vision_key or ""

        if region is not None:
            self.region = region
        else:
            self.region = settings.azure_ai_speech_region or "eastus"

        self.timeout = timeout

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        language: str = "en-US",
    ) -> SpeechTranscriptionResponse:
        """
        Transcribe audio bytes to text using Azure Speech REST endpoint.
        """
        if not audio_bytes:
            return SpeechTranscriptionResponse(
                text="", confidence=0.0, language=language
            )

        if not self.key:
            raise AzureSpeechOperationalError(
                "Azure Speech service key is not configured."
            )

        endpoint = f"https://{self.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        params = {
            "language": language,
            "format": "detailed",
        }

        # Normalize content-type header for Azure Speech short audio REST
        norm = content_type.lower()
        if "ogg" in norm:
            req_content_type = "audio/ogg; codecs=opus"
        elif "webm" in norm:
            req_content_type = "audio/webm; codecs=opus"
        elif "mpeg" in norm or "mp3" in norm:
            req_content_type = "audio/mpeg"
        else:
            req_content_type = "audio/wav; codecs=audio/pcm; samplerate=16000"

        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": req_content_type,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint, params=params, headers=headers, content=audio_bytes
                )
        except httpx.TimeoutException as exc:
            logger.warning("azure_speech_timeout", extra={"region": self.region})
            raise AzureSpeechOperationalError("Azure Speech transcription timed out.") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning("azure_speech_connect_failure", extra={"region": self.region})
            raise AzureSpeechOperationalError("Failed to connect to Azure Speech endpoint.") from exc
        except Exception as exc:
            logger.warning("azure_speech_request_failure", extra={"error": str(exc)})
            raise AzureSpeechOperationalError(f"Azure Speech request failed: {str(exc)}") from exc

        if response.status_code in (401, 403):
            logger.error("azure_speech_auth_failure", extra={"status_code": response.status_code})
            raise AzureSpeechOperationalError("Azure Speech authentication failed.")

        if response.status_code >= 500:
            logger.error("azure_speech_server_error", extra={"status_code": response.status_code})
            raise AzureSpeechOperationalError(
                f"Azure Speech service unavailable (status {response.status_code})."
            )

        if response.status_code != 200:
            logger.warning("azure_speech_error_response", extra={"status_code": response.status_code})
            raise AzureSpeechOperationalError(
                f"Azure Speech returned error (status {response.status_code}): {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise AzureSpeechOperationalError("Azure Speech returned malformed JSON.") from exc

        status = data.get("RecognitionStatus")
        if status == "Success":
            display_text = data.get("DisplayText") or ""
            nbest = data.get("NBest", [])
            confidence = 1.0
            if nbest and isinstance(nbest, list) and isinstance(nbest[0], dict):
                confidence = float(nbest[0].get("Confidence", 1.0))
                if not display_text:
                    display_text = nbest[0].get("Display", "")

            return SpeechTranscriptionResponse(
                text=display_text.strip(),
                confidence=round(confidence, 2),
                language=language,
            )
        elif status == "NoMatch":
            return SpeechTranscriptionResponse(
                text="", confidence=0.0, language=language
            )
        else:
            error_details = data.get("RecognitionStatus", "Unknown status")
            logger.warning("azure_speech_recognition_status", extra={"status": status})
            return SpeechTranscriptionResponse(
                text="", confidence=0.0, language=language
            )

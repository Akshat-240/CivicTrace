"""
test_azure_speech.py
====================
Unit and API route tests for Azure AI Speech transcription.
"""

import io
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.schemas.ai import SpeechTranscriptionResponse
from app.services.ai.speech import AzureSpeechOperationalError, AzureSpeechProvider


@pytest.mark.asyncio
class TestAzureSpeechProvider:
    async def test_empty_audio_returns_empty_transcription(self):
        provider = AzureSpeechProvider(key="mock-key", region="eastus")
        res = await provider.transcribe_audio(b"")
        assert res.text == ""
        assert res.confidence == 0.0

    async def test_unconfigured_key_raises_operational_error(self):
        provider = AzureSpeechProvider(key="", region="eastus")
        with pytest.raises(AzureSpeechOperationalError, match="not configured"):
            await provider.transcribe_audio(b"audio-data")

    async def test_successful_speech_transcription(self):
        provider = AzureSpeechProvider(key="mock-key", region="eastus")

        mock_stt_response = {
            "RecognitionStatus": "Success",
            "DisplayText": "There is a large pothole outside the school.",
            "NBest": [
                {
                    "Confidence": 0.96,
                    "Lexical": "there is a large pothole outside the school",
                    "Display": "There is a large pothole outside the school.",
                }
            ],
        }

        mock_http_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: mock_stt_response,
                "text": "OK",
            },
        )()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response

            audio_data = b"RIFF" + b"\x00" * 100
            result = await provider.transcribe_audio(
                audio_bytes=audio_data, content_type="audio/wav", language="en-US"
            )

            assert isinstance(result, SpeechTranscriptionResponse)
            assert result.text == "There is a large pothole outside the school."
            assert result.confidence == 0.96
            assert result.language == "en-US"

    async def test_speech_nomatch_returns_empty(self):
        provider = AzureSpeechProvider(key="mock-key", region="eastus")

        mock_stt_response = {"RecognitionStatus": "NoMatch"}
        mock_http_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: mock_stt_response,
                "text": "OK",
            },
        )()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response
            result = await provider.transcribe_audio(
                audio_bytes=b"audio-data", language="hi-IN"
            )
            assert result.text == ""
            assert result.confidence == 0.0
            assert result.language == "hi-IN"


@pytest.mark.asyncio
class TestSpeechTranscriptionRoute:
    async def test_transcribe_audio_endpoint_success(self, async_client: AsyncClient):
        mock_response = SpeechTranscriptionResponse(
            text="Garbage has been accumulating near the market entrance for three days.",
            confidence=0.92,
            language="en-US",
        )

        with patch(
            "app.services.ai.speech.AzureSpeechProvider.transcribe_audio",
            new_callable=AsyncMock,
        ) as mock_transcribe:
            mock_transcribe.return_value = mock_response

            audio_bytes = b"fake-audio-stream"
            files = {"file": ("voice.webm", io.BytesIO(audio_bytes), "audio/webm")}
            data = {"language": "en-US"}

            res = await async_client.post(
                "/api/v1/ai/transcribe",
                files=files,
                data=data,
            )

            assert res.status_code == 200
            payload = res.json()
            assert payload["text"] == "Garbage has been accumulating near the market entrance for three days."
            assert payload["confidence"] == 0.92
            assert payload["language"] == "en-US"

    async def test_transcribe_empty_file_returns_400(self, async_client: AsyncClient):
        files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
        res = await async_client.post("/api/v1/ai/transcribe", files=files)
        assert res.status_code == 400

    async def test_transcribe_service_unavailable_returns_503(
        self, async_client: AsyncClient
    ):
        with patch(
            "app.services.ai.speech.AzureSpeechProvider.transcribe_audio",
            side_effect=AzureSpeechOperationalError("Azure Speech service timed out"),
        ):
            files = {"file": ("voice.wav", io.BytesIO(b"audio-bytes"), "audio/wav")}
            res = await async_client.post("/api/v1/ai/transcribe", files=files)
            assert res.status_code == 503
            assert "unavailable" in res.json()["detail"].lower()

"""
AI routing endpoints (Perception & Speech-to-Text).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.ai import SpeechTranscriptionResponse
from app.services.ai.speech import AzureSpeechOperationalError, AzureSpeechProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

# Maximum allowed voice clip size (20MB)
MAX_VOICE_FILE_SIZE_BYTES = 20 * 1024 * 1024


@router.post(
    "/transcribe",
    response_model=SpeechTranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe spoken citizen problem briefing using Azure AI Speech",
)
async def transcribe_speech(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en-US"),
) -> SpeechTranscriptionResponse:
    """
    Accepts audio file upload from the citizen's browser microphone and converts
    speech into editable text using Azure AI Speech-to-Text.
    The audio recording is never permanently persisted.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    if len(content) > MAX_VOICE_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio recording exceeds maximum allowed size (20MB).",
        )

    provider = AzureSpeechProvider()
    try:
        return await provider.transcribe_audio(
            audio_bytes=content,
            content_type=file.content_type or "audio/wav",
            language=language or "en-US",
        )
    except AzureSpeechOperationalError as op_err:
        logger.warning("speech_transcription_service_error", extra={"error": str(op_err)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Speech transcription service is currently unavailable: {str(op_err)}",
        )
    except Exception as exc:
        logger.error("speech_transcription_unexpected_error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe speech audio: {str(exc)}",
        )

"""
AI schemas for perception layer.
"""

from typing import Any, Optional

from pydantic import Field

from app.models.enums import IssueType, SeverityLevel
from app.schemas.base import CivicBaseModel


class VisualPerceptionResult(CivicBaseModel):
    """
    Visual perception output from computer vision provider.
    """

    issue_category: Optional[IssueType] = Field(
        None, description="Visual-detected civic issue category."
    )
    description: Optional[str] = Field(
        None, description="Visual caption or description of the image."
    )
    severity: Optional[SeverityLevel] = Field(
        None, description="Assessed visual severity level."
    )
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Visual confidence score."
    )
    tags: list[str] = Field(
        default_factory=list, description="Visual tags extracted from image."
    )
    detected_objects: list[str] = Field(
        default_factory=list, description="Objects detected in image."
    )
    safety_risk_detected: bool = Field(
        False, description="True if visual safety hazard was detected."
    )
    provider: str = Field(
        "azure_computer_vision", description="Visual perception provider identifier."
    )


class LanguagePerceptionResult(CivicBaseModel):
    """
    Textual perception output from language analysis provider.
    """

    status: str = Field(
        "success", description="Perception status: success | skipped | unavailable | error."
    )
    detected_category: Optional[IssueType] = Field(
        None, description="Text-derived civic issue category."
    )
    issue_terms: list[str] = Field(
        default_factory=list, description="Extracted civic issue keywords/terms."
    )
    key_phrases: list[str] = Field(
        default_factory=list, description="Key phrases extracted from written briefing."
    )
    entities: list[dict[str, Any]] = Field(
        default_factory=list, description="Named entities and categories recognized in text."
    )
    impact_phrases: list[str] = Field(
        default_factory=list, description="Phrases indicating severity, impact, or urgency."
    )
    safety_risk_detected: bool = Field(
        False, description="True if language indicates safety hazards or dangers."
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score if provided by the language provider."
    )
    summary: Optional[str] = Field(
        None, description="Summary or normalized representation of the briefing."
    )
    provider: str = Field(
        "azure_ai_language", description="Language perception provider identifier."
    )


class SpeechTranscriptionResponse(CivicBaseModel):
    """
    Speech-to-text response from Azure AI Speech.
    """

    text: str = Field(..., description="Transcribed text from speech audio.")
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Transcription confidence score."
    )
    language: str = Field(
        "en-US", description="Language locale used for transcription."
    )


class AIAnalysisResult(CivicBaseModel):
    """
    Structured output from the AI Perception layer.
    """

    civic_issue_category: Optional[IssueType] = Field(
        None, description="The identified civic issue category if clear."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score between 0.0 and 1.0."
    )
    severity_assessment: Optional[SeverityLevel] = Field(
        None, description="Assessed severity of the issue."
    )
    safety_risk_detected: bool = Field(
        False, description="True if a clear physical safety risk to humans is detected."
    )
    ambiguity_flag: bool = Field(
        False, description="True if the evidence is blurry, missing, or unclear."
    )
    ambiguity_reason: Optional[str] = Field(
        None, description="Explanation of why the evidence is ambiguous, if flagged."
    )
    extracted_attributes: dict[str, Any] = Field(
        default_factory=dict, description="Key-value pairs of extracted details."
    )
    explanation: str = Field(
        ..., description="Brief explanation of the reasoning."
    )
    visual_perception: Optional[VisualPerceptionResult] = Field(
        None, description="Structured visual perception details."
    )
    language_perception: Optional[LanguagePerceptionResult] = Field(
        None, description="Structured language perception details from written briefing."
    )
    combined_interpretation: Optional[str] = Field(
        None, description="Synthesized multi-modal perception summary."
    )

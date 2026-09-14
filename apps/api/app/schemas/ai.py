"""
AI schemas for perception layer.
"""

from typing import Any, Optional

from pydantic import Field

from app.models.enums import IssueType, SeverityLevel
from app.schemas.base import CivicBaseModel


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

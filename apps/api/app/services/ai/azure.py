"""
Azure Computer Vision provider for AI Perception.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import CivicTraceError, ServiceUnavailableError
from app.models.enums import IssueType, SeverityLevel
from app.schemas.ai import AIAnalysisResult, VisualPerceptionResult
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)


class AzureOperationalError(ServiceUnavailableError):
    """Raised when an operational failure occurs communicating with Azure Computer Vision."""
    error_code = "AZURE_OPERATIONAL_ERROR"


# Priority-ordered mapping: (list_of_indicators, IssueType)
CATEGORY_RULES: list[tuple[list[str], IssueType]] = [
    (["pothole", "potholes"], IssueType.POTHOLE),
    (["graffiti"], IssueType.GRAFFITI),
    (["flooding", "flood", "waterlogging", "standing water", "puddle", "submerged"], IssueType.FLOODING),
    (["garbage", "trash", "dumping", "waste", "litter", "rubbish", "refuse", "debris", "junkyard"], IssueType.ILLEGAL_DUMPING),
    (["streetlight", "street light", "lamp post", "lantern", "lighting fixture"], IssueType.BROKEN_STREETLIGHT),
    (["sewage", "sewer", "manhole overflow", "drain overflow"], IssueType.SEWAGE_OVERFLOW),
    (["water leak", "pipeline leak", "burst pipe", "pipe burst", "broken pipe"], IssueType.WATER_LEAK),
    (["road damage", "damaged road", "cracked road", "asphalt crack", "asphalt damage", "caved in", "subsidence", "sinkhole"], IssueType.ROAD_DAMAGE),
    (["traffic sign", "street sign", "damaged sign", "billboard", "signage"], IssueType.DAMAGED_SIGNAGE),
    (["overgrown vegetation", "fallen tree", "overgrowth", "wild bush"], IssueType.OVERGROWN_VEGETATION),
    (["abandoned vehicle", "abandoned car", "car wreck", "wrecked car"], IssueType.ABANDONED_VEHICLE),
]

SAFETY_HAZARD_KEYWORDS = {
    "fire", "smoke", "spark", "sparking", "arcing", "live wire", "exposed wire",
    "hazard", "danger", "dangerous", "emergency", "sinkhole", "collapse",
    "collision", "accident", "electrical hazard",
}

HIGH_SEVERITY_KEYWORDS = {
    "severe", "heavy", "massive", "collapse", "burst", "sinkhole", "danger",
    "hazard", "critical", "deep", "emergency",
}


class AzureVisionProvider(AIProvider):
    """
    Implements AIProvider using the Azure Computer Vision v3.2 Analyze API.
    Provides visual feature extraction, keyword-anchored issue categorization,
    and deterministic structured output conforming to AIAnalysisResult.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        timeout: float = 15.0,
    ):
        settings = get_settings()
        self.endpoint = (endpoint or settings.azure_ai_vision_endpoint or "").rstrip("/")
        self.key = key or settings.azure_ai_vision_key or ""
        self.timeout = timeout
        self._cache: dict[str, AIAnalysisResult] = {}

    def _hash_input(self, description: Optional[str], media_urls: list[str]) -> str:
        """Create a deterministic hash for in-memory caching."""
        hasher = hashlib.sha256()
        if description:
            hasher.update(description.encode("utf-8"))
        for url in sorted(media_urls):
            hasher.update(url.encode("utf-8"))
        return hasher.hexdigest()

    async def analyze_evidence(
        self, description: Optional[str], media_urls: list[str]
    ) -> AIAnalysisResult:
        """
        Analyze visual evidence using Azure Computer Vision.
        Raises AzureOperationalError on connectivity, auth, or service failures.
        """
        cache_key = self._hash_input(description, media_urls)
        if cache_key in self._cache:
            logger.info("azure_vision_cache_hit", extra={"cache_key": cache_key})
            return self._cache[cache_key]

        if not self.endpoint or not self.key:
            raise AzureOperationalError("Azure Computer Vision endpoint or key is not configured.")

        # Media validation
        valid_media_urls = [u for u in media_urls if u and not u.startswith("synthetic://")]
        if not valid_media_urls:
            # If evidence has only synthetic URIs or no media, Azure cannot process it
            raise AzureOperationalError(
                "No valid visual media URL provided for Azure Computer Vision analysis."
            )

        target_url = valid_media_urls[0]
        api_url = f"{self.endpoint}/vision/v3.2/analyze?visualFeatures=Categories,Description,Objects,Tags"
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json",
        }
        payload = {"url": target_url}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.warning("azure_vision_timeout", extra={"endpoint": self.endpoint})
            raise AzureOperationalError("Azure Computer Vision request timed out.") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning("azure_vision_connection_failure", extra={"endpoint": self.endpoint})
            raise AzureOperationalError("Failed to connect to Azure Computer Vision endpoint.") from exc
        except Exception as exc:
            logger.warning("azure_vision_request_failure", extra={"error": str(exc)})
            raise AzureOperationalError(f"Azure Computer Vision request failure: {str(exc)}") from exc

        # Handle HTTP status errors
        if response.status_code in (401, 403):
            logger.error("azure_vision_auth_failure", extra={"status_code": response.status_code})
            raise AzureOperationalError("Azure Computer Vision authentication failed.")

        if response.status_code >= 500:
            logger.error("azure_vision_server_error", extra={"status_code": response.status_code})
            raise AzureOperationalError(
                f"Azure Computer Vision service unavailable (status {response.status_code})."
            )

        if response.status_code != 200:
            error_msg = response.text[:200]
            logger.warning("azure_vision_error_response", extra={"status_code": response.status_code})
            raise AzureOperationalError(
                f"Azure Computer Vision returned error (status {response.status_code}): {error_msg}"
            )

        try:
            raw_data = response.json()
        except Exception as exc:
            raise AzureOperationalError("Azure Computer Vision returned malformed JSON.") from exc

        result = self._parse_azure_response(raw_data, description)
        self._cache[cache_key] = result
        return result

    def _parse_azure_response(
        self, raw_data: dict[str, Any], description: Optional[str]
    ) -> AIAnalysisResult:
        """
        Deterministically convert raw Azure Computer Vision response into
        a strictly-typed CivicTrace AIAnalysisResult.
        """
        # 1. Tags
        tags_raw = raw_data.get("tags", [])
        tag_dict: dict[str, float] = {}
        for t in tags_raw:
            if isinstance(t, dict) and "name" in t:
                tag_dict[str(t["name"]).lower().strip()] = float(t.get("confidence", 0.0))

        # 2. Captions
        description_block = raw_data.get("description", {})
        captions = description_block.get("captions", [])
        top_caption: Optional[str] = None
        caption_confidence: float = 0.0
        if captions and isinstance(captions, list) and isinstance(captions[0], dict):
            top_caption = captions[0].get("text")
            caption_confidence = float(captions[0].get("confidence", 0.0))

        desc_tags = [str(t).lower().strip() for t in description_block.get("tags", [])]

        # 3. Objects
        objects_raw = raw_data.get("objects", [])
        detected_objects: list[str] = []
        for o in objects_raw:
            if isinstance(o, dict) and "object" in o:
                detected_objects.append(str(o["object"]).lower().strip())

        # Combine text indicators for matching
        combined_text_tokens = set(tag_dict.keys()) | set(desc_tags) | set(detected_objects)
        caption_lower = (top_caption or "").lower()

        # 4. Civic Issue Category determination
        matched_category: Optional[IssueType] = None
        matched_confidence: float = 0.0

        for keywords, issue_type in CATEGORY_RULES:
            for kw in keywords:
                if kw in combined_text_tokens or (kw in caption_lower):
                    matched_category = issue_type
                    # Confidence from tag or caption
                    conf = tag_dict.get(kw, caption_confidence)
                    if conf > matched_confidence:
                        matched_confidence = conf
            if matched_category is not None:
                break

        # If no category matched, calculate baseline confidence from top caption / tags
        if matched_category is None:
            max_tag_conf = max(tag_dict.values(), default=0.0)
            overall_confidence = max(caption_confidence, max_tag_conf)
        else:
            overall_confidence = max(matched_confidence, 0.40)

        # Clamp confidence to [0.0, 1.0]
        final_confidence = min(max(round(overall_confidence, 4), 0.0), 1.0)

        # 5. Safety risk detection
        safety_risk_detected = any(
            kw in combined_text_tokens or kw in caption_lower
            for kw in SAFETY_HAZARD_KEYWORDS
        )

        # 6. Severity assessment
        severity_assessment: Optional[SeverityLevel] = None
        if matched_category is not None:
            has_severe_indicator = any(
                kw in combined_text_tokens or kw in caption_lower
                for kw in HIGH_SEVERITY_KEYWORDS
            )
            if has_severe_indicator or safety_risk_detected:
                severity_assessment = SeverityLevel.HIGH
            elif final_confidence >= 0.70:
                severity_assessment = SeverityLevel.MEDIUM
            else:
                severity_assessment = SeverityLevel.LOW

        # 7. Ambiguity flag and reason
        if matched_category is None:
            ambiguity_flag = True
            ambiguity_reason = "Visual evidence lacks recognizable civic issue features."
        elif final_confidence < 0.40:
            ambiguity_flag = True
            ambiguity_reason = f"Low visual perception confidence ({final_confidence:.2f})."
        else:
            ambiguity_flag = False
            ambiguity_reason = None

        # 8. Extracted attributes
        extracted_attributes: dict[str, Any] = {
            "tags": list(tag_dict.keys())[:15],
            "caption": top_caption,
            "caption_confidence": caption_confidence if top_caption else None,
            "detected_objects": detected_objects,
            "provider": "azure_computer_vision",
            "api_version": "v3.2",
        }

        # 9. Explanation
        if top_caption:
            explanation = (
                f"Azure Computer Vision visual observation: {top_caption} "
                f"(confidence: {caption_confidence:.2f})."
            )
        elif tag_dict:
            top_tags = list(tag_dict.keys())[:5]
            explanation = f"Azure Computer Vision detected visual tags: {', '.join(top_tags)}."
        # 10. Structured Visual Perception
        visual_perception = VisualPerceptionResult(
            issue_category=matched_category,
            description=top_caption,
            severity=severity_assessment,
            confidence=final_confidence,
            tags=list(tag_dict.keys())[:15],
            detected_objects=detected_objects,
            safety_risk_detected=safety_risk_detected,
            provider="azure_computer_vision",
        )

        try:
            return AIAnalysisResult(
                civic_issue_category=matched_category,
                confidence=final_confidence,
                severity_assessment=severity_assessment,
                safety_risk_detected=safety_risk_detected,
                ambiguity_flag=ambiguity_flag,
                ambiguity_reason=ambiguity_reason,
                extracted_attributes=extracted_attributes,
                explanation=explanation,
                visual_perception=visual_perception,
            )
        except ValidationError as val_err:
            logger.error("azure_vision_validation_failed", exc_info=True)
            raise AzureOperationalError(f"Azure response validation failed: {str(val_err)}") from val_err

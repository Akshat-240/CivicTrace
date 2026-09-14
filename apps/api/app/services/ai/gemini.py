"""
Gemini API provider for AI Perception.
"""

import hashlib
import json
import logging
import re
from typing import Optional

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import CivicTraceError
from app.schemas.ai import AIAnalysisResult
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)


class GeminiAIProvider(AIProvider):
    """
    Implements AIProvider using the google-genai SDK.
    """

    def __init__(self):
        settings = get_settings()
        self.model = settings.gemini_model
        self.api_key = settings.gemini_api_key

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            try:
                self.client = genai.Client()
            except Exception:
                self.client = None

        # Simple deterministic cache (in-memory for MVP)
        self._cache: dict[str, AIAnalysisResult] = {}

    def _hash_input(self, description: Optional[str], media_urls: list[str]) -> str:
        """Create a deterministic hash for caching."""
        hasher = hashlib.sha256()
        if description:
            hasher.update(description.encode("utf-8"))
        for url in sorted(media_urls):
            hasher.update(url.encode("utf-8"))
        return hasher.hexdigest()

    async def analyze_evidence(
        self, description: Optional[str], media_urls: list[str]
    ) -> AIAnalysisResult:
        if not self.client:
            from app.core.errors import ServiceUnavailableError
            raise ServiceUnavailableError("Gemini API key is not configured.")

        cache_key = self._hash_input(description, media_urls)
        if cache_key in self._cache:
            logger.info("ai_perception_cache_hit", extra={"cache_key": cache_key})
            return self._cache[cache_key]

        prompt = self._build_prompt(description)
        # Note: In MVP we only use text since we might not have real URLs accessible to Gemini,
        # but if we do, we'd pass them. For now we only pass the prompt.
        contents = [prompt]
        if media_urls:
            # We would typically download or provide parts here.
            # We skip passing raw URLs directly to contents unless supported.
            # We just append them to the text prompt as context.
            urls_context = "Media provided:\n" + "\n".join(media_urls)
            contents.append(urls_context)

        try:
            # We use structured output format. The google-genai SDK supports
            # JSON schema validation via response_schema.
            schema = AIAnalysisResult.model_json_schema()
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0, # Deterministic
                ),
            )
            
            if not response.text:
                raise CivicTraceError(
                    "AI provider returned empty response", code="AI_PROVIDER_ERROR"
                )

            # Clean JSON if wrapped in markdown
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed_data = json.loads(raw_text.strip())
            result = AIAnalysisResult(**parsed_data)
            
            self._cache[cache_key] = result
            return result

        except ValidationError as e:
            logger.error("ai_perception_validation_failed", exc_info=True)
            class AIValidationError(CivicTraceError):
                error_code = "AI_VALIDATION_ERROR"
                status_code = 422
            raise AIValidationError("AI response failed schema validation", detail={"errors": e.errors()})
        except Exception as e:
            # Handle rate limits, network errors, etc.
            logger.error("ai_perception_provider_failed", exc_info=True)
            from app.core.errors import ServiceUnavailableError
            raise ServiceUnavailableError(f"AI provider error: {str(e)}")

    def _build_prompt(self, description: Optional[str]) -> str:
        return f"""
You are analyzing evidence for a civic issue reporting system.
Your job is pure perception and structured extraction.

RULES:
1. You may identify the likely civic issue, extract relevant attributes, estimate severity, identify safety risk, and provide confidence.
2. You MUST NOT assign responsible authority, determine jurisdiction, decide SLA, declare accountability, or invent facts.
3. If evidence is insufficient, blurry, or missing, set ambiguity_flag=true, provide an ambiguity_reason, and do not hallucinate missing information.
4. Confidence must reflect how clear the evidence is.
5. If you cannot determine the civic_issue_category, leave it null.

User Description of the issue:
{description or "No description provided."}

Return a valid JSON strictly matching the requested schema.
"""

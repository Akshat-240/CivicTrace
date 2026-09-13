"""
AI Service orchestration.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ConflictError, NotFoundError, ServiceUnavailableError
from app.models.enums import EvidenceStatus
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.ai import AIAnalysisResult
from app.services.ai.azure import AzureOperationalError, AzureVisionProvider
from app.services.ai.base import AIProvider
from app.services.ai.gemini import GeminiAIProvider
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class AIService:
    """
    Orchestrates the AI perception pipeline for evidence.
    Supports primary provider (Azure Computer Vision) with automated fallback
    (Gemini) strictly upon operational provider failures.
    """

    def __init__(
        self,
        session: AsyncSession,
        provider: Optional[AIProvider] = None,
        fallback_provider: Optional[AIProvider] = None,
        storage_service: Optional[StorageService] = None,
    ):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        self.storage_service = storage_service or StorageService()
        settings = get_settings()

        if provider is not None:
            self.primary_provider = provider
            self.fallback_provider = fallback_provider
        else:
            self.primary_provider, self.fallback_provider = self._resolve_providers(settings)

    @property
    def provider(self) -> AIProvider:
        """Backward compatibility alias for self.primary_provider."""
        return self.primary_provider

    @provider.setter
    def provider(self, val: AIProvider) -> None:
        self.primary_provider = val

    def _resolve_providers(
        self, settings: Settings
    ) -> tuple[AIProvider, Optional[AIProvider]]:
        primary_type = (settings.ai_primary_provider or "azure").lower().strip()
        fallback_type = (settings.ai_fallback_provider or "gemini").lower().strip()

        def _build(name: str) -> Optional[AIProvider]:
            if name == "azure":
                if settings.azure_ai_vision_endpoint and settings.azure_ai_vision_key:
                    return AzureVisionProvider(
                        endpoint=settings.azure_ai_vision_endpoint,
                        key=settings.azure_ai_vision_key,
                    )
                logger.warning("azure_ai_vision_unconfigured_cannot_build_provider")
                return None
            elif name == "gemini":
                return GeminiAIProvider()
            return None

        primary = _build(primary_type)
        fallback = _build(fallback_type)

        if primary is None:
            if fallback is not None:
                logger.info(
                    "primary_provider_unconfigured_using_fallback_as_primary",
                    extra={"provider": fallback_type},
                )
                primary = fallback
                fallback = None
            else:
                primary = GeminiAIProvider()

        return primary, fallback

    async def _resolve_media_urls(self, storage_key: Optional[str]) -> list[str]:
        """
        Resolve evidence storage key to signed media URL.
        Guarantees that synthetic:// seed URIs are NEVER sent to external AI services.
        """
        if not storage_key:
            return []

        if storage_key.startswith("synthetic://"):
            logger.info("skipping_external_ai_for_synthetic_evidence", extra={"storage_key": storage_key})
            return []

        # Real Supabase storage key: generate temporary signed URL
        try:
            return [await self.storage_service.create_signed_url(storage_key, expires_in=300)]
        except Exception as exc:
            logger.warning(
                "failed_to_create_signed_url_for_evidence",
                extra={"storage_key": storage_key, "error": str(exc)},
            )
            return []

    async def process_evidence(self, evidence_id: uuid.UUID) -> AIAnalysisResult:
        """
        Orchestrate the AI perception pipeline for a given evidence item.
        Executes primary provider with operational fallback to secondary.
        Updates the evidence record with the extracted structured result.
        """
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        if evidence.status not in (EvidenceStatus.PENDING, EvidenceStatus.FAILED):
            raise ConflictError(
                f"Evidence {evidence_id} is in status {evidence.status}, cannot process."
            )

        # Mark as processing
        evidence.status = EvidenceStatus.PROCESSING
        self.session.add(evidence)
        await self.session.commit()

        media_urls = await self._resolve_media_urls(evidence.storage_key)

        result: Optional[AIAnalysisResult] = None
        try:
            try:
                # Primary execution
                result = await self.primary_provider.analyze_evidence(
                    description=evidence.description, media_urls=media_urls
                )
            except (AzureOperationalError, ServiceUnavailableError) as op_err:
                # Fallback strictly for operational failures
                logger.warning(
                    "primary_ai_provider_operational_failure_triggering_fallback",
                    extra={
                        "evidence_id": str(evidence_id),
                        "error": str(op_err),
                        "fallback_available": self.fallback_provider is not None,
                    },
                )
                if self.fallback_provider is not None:
                    result = await self.fallback_provider.analyze_evidence(
                        description=evidence.description, media_urls=media_urls
                    )
                else:
                    raise op_err

            # Map the validated result back to the ORM model
            evidence.ai_category = result.civic_issue_category.value if result.civic_issue_category else None
            evidence.ai_confidence = result.confidence
            evidence.ai_severity_raw = result.severity_assessment.value if result.severity_assessment else None
            evidence.ai_safety_risk = result.safety_risk_detected
            evidence.ai_perception_payload = result.model_dump(mode="json")
            evidence.ai_ambiguity_flag = result.ambiguity_flag
            evidence.ai_ambiguity_reason = result.ambiguity_reason

            # Transition state
            evidence.status = EvidenceStatus.PROCESSED

            self.session.add(evidence)
            await self.session.commit()

            return result

        except Exception as e:
            # On failure of both providers, revert to FAILED state and bubble up error
            evidence.status = EvidenceStatus.FAILED
            self.session.add(evidence)
            await self.session.commit()
            raise e

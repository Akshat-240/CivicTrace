"""
AI Service orchestration.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CivicTraceError, NotFoundError
from app.models.enums import EvidenceStatus
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.ai import AIAnalysisResult
from app.services.ai.base import AIProvider
from app.services.ai.gemini import GeminiAIProvider


class AIService:
    def __init__(self, session: AsyncSession, provider: Optional[AIProvider] = None):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        # Dependency injection for tests/overrides, fallback to Gemini
        self.provider = provider or GeminiAIProvider()

    async def process_evidence(self, evidence_id: uuid.UUID) -> AIAnalysisResult:
        """
        Orchestrate the AI perception pipeline for a given evidence item.
        Updates the evidence record with the extracted structured result.
        """
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        if evidence.status not in (EvidenceStatus.PENDING, EvidenceStatus.FAILED):
            # Only process pending or previously failed evidence
            from app.core.errors import ConflictError
            raise ConflictError(
                f"Evidence {evidence_id} is in status {evidence.status}, cannot process."
            )

        # Mark as processing
        evidence.status = EvidenceStatus.PROCESSING
        self.session.add(evidence)
        await self.session.commit()

        # Prepare media URLs (if we had real signed URLs, we'd fetch them)
        media_urls = []
        if evidence.storage_key:
            media_urls.append(evidence.storage_key)

        try:
            # Execute perception via the provider
            result = await self.provider.analyze_evidence(
                description=evidence.description, media_urls=media_urls
            )

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
            # On failure, revert to FAILED state and bubble up error
            evidence.status = EvidenceStatus.FAILED
            self.session.add(evidence)
            await self.session.commit()
            raise e

"""
Resolution Verification Engine.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import (
    AccountabilityState,
    EventType,
    EvidenceStatus,
    EvidenceType,
    IncidentStatus,
    SeverityLevel,
    VerificationResult,
)
from app.models.event import IncidentEvent
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.sla import SLA
from app.models.verification import VerificationRecord


class VerificationConfig:
    SEVERITY_VALUES = {
        SeverityLevel.CRITICAL: 4,
        SeverityLevel.HIGH: 3,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.LOW: 1,
    }


class VerificationService:
    """
    Phase 5 three-stage verification engine.

    Stage 1 - submit_resolution():
        Authority submits resolution evidence. Incident moves ACTIVE -> UNDER_REVIEW.

    Stage 2 - verify_resolution():
        Automatic evidence evaluation. Produces VerificationResult + confidence.
        Does NOT change incident.status -- evaluation is advisory only.
        verified_by = "system".

    Stage 3 - human_verify():
        Human reviewer makes an explicit decision. Only this method changes
        incident.status. verified_by = reviewer identity (demo MVP -- no real auth).
        Requires resolution evidence to exist (Test N invariant).
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = VerificationConfig()

    # ------------------------------------------------------------------
    # Stage 1 -- Resolution Submission
    # ------------------------------------------------------------------

    async def submit_resolution(
        self,
        incident_id: uuid.UUID,
        description: str,
        evidence_type: EvidenceType = EvidenceType.TEXT,
    ) -> Evidence:
        """
        Authority submits resolution evidence for an ACTIVE incident.

        - Creates Evidence with is_verification_evidence=True.
        - Transitions incident: ACTIVE -> UNDER_REVIEW.
        - Records EVIDENCE_SUBMITTED + VERIFICATION_SUBMITTED timeline events.
        - Uses flush() only -- get_db() commits the transaction at request end.
        """
        from app.core.errors import ConflictError

        stmt = (
            select(Incident)
            .options(selectinload(Incident.evidence_items))
            .where(Incident.id == incident_id)
        )
        result = await self.session.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        _TERMINAL = {IncidentStatus.CLOSED, IncidentStatus.INVALID}
        _ALREADY_IN_REVIEW = {IncidentStatus.RESOLVED, IncidentStatus.UNDER_REVIEW}

        if incident.status in _TERMINAL:
            raise ConflictError(
                f"Cannot submit resolution evidence for incident in terminal state: "
                f"{incident.status.value}"
            )
        if incident.status in _ALREADY_IN_REVIEW:
            raise ConflictError(
                f"Cannot submit resolution evidence: incident is already "
                f"{incident.status.value}. Only ACTIVE incidents accept new resolution submissions."
            )

        # NOTE: No binary storage in MVP -- text/metadata evidence only.
        evidence = Evidence(
            incident_id=incident.id,
            evidence_type=evidence_type,
            status=EvidenceStatus.PENDING,
            is_verification_evidence=True,
            description=description,
        )
        self.session.add(evidence)
        await self.session.flush()

        incident.evidence_count = (incident.evidence_count or 0) + 1
        incident.status = IncidentStatus.UNDER_REVIEW

        self.session.add(IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.EVIDENCE_SUBMITTED,
            actor="authority",
            summary="Resolution evidence submitted by authority.",
            payload={"evidence_id": str(evidence.id), "evidence_type": evidence_type.value},
        ))
        self.session.add(IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.VERIFICATION_SUBMITTED,
            actor="authority",
            summary="Resolution submitted. Incident moved to UNDER_REVIEW for verification.",
            payload={"previous_status": "active", "new_status": "under_review"},
        ))

        await self.session.flush()
        return evidence

    # ------------------------------------------------------------------
    # Stage 2 -- Automatic Evidence Evaluation
    # ------------------------------------------------------------------

    async def verify_resolution(self, incident_id: uuid.UUID) -> VerificationRecord:
        """
        Automatic evidence-based evaluation.

        IMPORTANT: This method is EVALUATION ONLY. It does NOT change
        incident.status. Status transitions are the exclusive responsibility
        of human_verify(). verified_by is always "system".

        The existing commit() is preserved for Gate 3/4 test compatibility.
        """
        from app.core.errors import ConflictError

        now = datetime.now(timezone.utc)

        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.evidence_items),
                selectinload(Incident.verification),
                selectinload(Incident.priority),
                selectinload(Incident.sla),
            )
            .where(Incident.id == incident_id)
        )
        result = await self.session.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        # Guard: reject terminal states
        if incident.status in (IncidentStatus.CLOSED, IncidentStatus.INVALID):
            raise ConflictError(
                f"Cannot run automatic evaluation for incident in state: {incident.status.value}"
            )

        # 1. Split evidence
        before_ev = []
        after_ev = []

        for ev in incident.evidence_items:
            if ev.status != EvidenceStatus.PROCESSED:
                continue
            if ev.is_verification_evidence:
                after_ev.append(ev)
            else:
                before_ev.append(ev)

        # 2. Determine Original Severity
        orig_sev_val = 0
        if incident.priority and incident.priority.severity:
            orig_sev_val = self.config.SEVERITY_VALUES.get(incident.priority.severity, 0)
        else:
            for ev in before_ev:
                if ev.ai_severity_raw:
                    try:
                        sev_enum = SeverityLevel(ev.ai_severity_raw.lower())
                        val = self.config.SEVERITY_VALUES.get(sev_enum, 0)
                        if val > orig_sev_val:
                            orig_sev_val = val
                    except ValueError:
                        pass

        if orig_sev_val == 0:
            orig_sev_val = 1

        # 3. Evaluate After Evidence
        has_valid_after = False
        outcome = VerificationResult.FULLY_RESOLVED
        explanation = ""

        if not after_ev:
            outcome = VerificationResult.INSUFFICIENT_EVIDENCE
            explanation = "No verification evidence submitted."
        else:
            related_count = 0
            for ev in after_ev:
                if ev.ai_ambiguity_flag:
                    continue

                has_valid_after = True

                if ev.ai_category != incident.issue_type:
                    pass
                else:
                    related_count += 1
                    if ev.ai_severity_raw and ev.ai_severity_raw.lower() == "none":
                        ev_sev_val = 0
                    else:
                        ev_sev_val = 1
                        if ev.ai_severity_raw:
                            try:
                                sev_enum = SeverityLevel(ev.ai_severity_raw.lower())
                                ev_sev_val = self.config.SEVERITY_VALUES.get(sev_enum, 1)
                            except ValueError:
                                pass

                    if ev_sev_val >= orig_sev_val:
                        outcome = VerificationResult.UNRESOLVED
                    elif ev_sev_val > 0 and ev_sev_val < orig_sev_val and outcome != VerificationResult.UNRESOLVED:
                        outcome = VerificationResult.PARTIALLY_RESOLVED

            if not has_valid_after:
                outcome = VerificationResult.INSUFFICIENT_EVIDENCE
                explanation = "All submitted verification evidence was flagged as ambiguous or unusable."
            elif related_count == 0:
                outcome = VerificationResult.INSUFFICIENT_EVIDENCE
                explanation = "Verification evidence category does not match the incident. Cannot confirm resolution."
            else:
                if outcome == VerificationResult.FULLY_RESOLVED:
                    explanation = "Evidence supports complete resolution of the issue."
                elif outcome == VerificationResult.PARTIALLY_RESOLVED:
                    explanation = "Evidence shows improvement, but the issue remains partially present."
                else:
                    explanation = "Evidence shows the issue is unresolved and severity has not improved."

        # 4. Upsert VerificationRecord
        record = incident.verification
        if not record:
            record = VerificationRecord(
                incident_id=incident.id,
                before_evidence_id=before_ev[-1].id if before_ev else None,
                after_evidence_id=after_ev[-1].id if after_ev else None,
            )
            incident.verification = record
            self.session.add(record)

        record.result = outcome
        record.explanation = explanation
        record.verified_by = "system"
        record.verified_at = now
        record.confidence = 0.9 if has_valid_after else 0.0

        # NO incident.status change -- evaluation is advisory only.
        # Status transitions are exclusively handled by human_verify().

        # 5. Timeline Event
        self.session.add(IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.VERIFICATION_RESULT_SET,
            actor="system",
            summary=f"Automatic evaluation completed: {outcome.value.upper()}. {explanation}",
            payload={"result": outcome.value, "confidence": record.confidence, "verified_by": "system"},
        ))

        await self.session.commit()
        return record

    # ------------------------------------------------------------------
    # Stage 3 -- Human Verification Decision
    # ------------------------------------------------------------------

    async def human_verify(
        self,
        incident_id: uuid.UUID,
        result: VerificationResult,
        explanation: Optional[str] = None,
        verified_by: Optional[str] = None,
    ) -> VerificationRecord:
        """
        Human reviewer makes an explicit verification decision.

        Guards:
        - Incident must be UNDER_REVIEW.
        - At least one resolution evidence (is_verification_evidence=True) must exist.
          This prevents approving FULLY_RESOLVED without actual evidence (Test N).

        Status transitions (only FULLY_RESOLVED unlocks RESOLVED):
        - FULLY_RESOLVED         -> RESOLVED  (+ SLA resolved)
        - INSUFFICIENT_EVIDENCE  -> ACTIVE    (returns to open workflow)
        - UNRESOLVED             -> ACTIVE    (issue still exists)
        - PARTIALLY_RESOLVED     -> stays UNDER_REVIEW (more evidence needed)

        Uses flush() only -- get_db() commits at request end.
        verified_by defaults to "demo-authority-reviewer" (no real auth in MVP).
        """
        from app.core.errors import ConflictError

        now = datetime.now(timezone.utc)
        # Demo reviewer identity -- not real authentication.
        reviewer = (verified_by or "").strip() or "demo-authority-reviewer"

        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.evidence_items),
                selectinload(Incident.verification),
                selectinload(Incident.sla),
            )
            .where(Incident.id == incident_id)
        )
        db_result = await self.session.execute(stmt)
        incident = db_result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        # Guard: terminal states.
        if incident.status in (IncidentStatus.CLOSED, IncidentStatus.INVALID):
            raise ConflictError(
                f"Cannot human-verify incident in terminal state: {incident.status.value}"
            )
        # Guard: must be UNDER_REVIEW.
        if incident.status != IncidentStatus.UNDER_REVIEW:
            raise ConflictError(
                f"Human verification requires incident status UNDER_REVIEW. "
                f"Current status: {incident.status.value}. "
                f"Use submit-resolution first."
            )

        # Guard (Test N): resolution evidence must exist.
        resolution_evidence = [
            ev for ev in incident.evidence_items
            if ev.is_verification_evidence
        ]
        if not resolution_evidence:
            raise ConflictError(
                "Human verification rejected: no resolution evidence has been submitted. "
                "Call submit-resolution first to provide resolution evidence."
            )

        # Upsert VerificationRecord (unique=True on incident_id enforced by DB).
        record = incident.verification
        if not record:
            record = VerificationRecord(
                incident_id=incident.id,
                before_evidence_id=None,
                after_evidence_id=resolution_evidence[-1].id,
            )
            incident.verification = record
            self.session.add(record)
        else:
            record.after_evidence_id = resolution_evidence[-1].id

        record.result = result
        record.explanation = explanation or f"Human decision: {result.value}"
        record.verified_by = reviewer
        record.verified_at = now
        # Human decision carries maximum confidence -- a reviewer examined the evidence.
        record.confidence = 1.0

        # Status transitions.
        if result == VerificationResult.FULLY_RESOLVED:
            incident.status = IncidentStatus.RESOLVED
            if incident.sla and incident.sla.state != AccountabilityState.RESOLVED:
                incident.sla.state = AccountabilityState.RESOLVED
                incident.sla.resolved_at = now
        elif result in (VerificationResult.INSUFFICIENT_EVIDENCE, VerificationResult.UNRESOLVED):
            incident.status = IncidentStatus.ACTIVE
        # PARTIALLY_RESOLVED -> stays UNDER_REVIEW. Does NOT unlock RESOLVED/CLOSED.

        # Timeline event -- actor is the human reviewer, not "system".
        self.session.add(IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.VERIFICATION_RESULT_SET,
            actor=reviewer,
            summary=f"Human verification decision: {result.value.upper()}. {record.explanation}",
            payload={
                "result": result.value,
                "verified_by": reviewer,
                "confidence": record.confidence,
            },
        ))

        await self.session.flush()
        return record

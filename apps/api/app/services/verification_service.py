"""
Resolution Verification Engine.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import AccountabilityState, EventType, EvidenceStatus, IncidentStatus, SeverityLevel, VerificationResult
from app.models.event import IncidentEvent
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
    Evaluates before/after evidence to determine resolution status.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = VerificationConfig()

    async def verify_resolution(self, incident_id: uuid.UUID) -> VerificationRecord:
        """
        Executes verification logic for the given incident.
        """
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
        # Either from Priority model or compute from before_evidence
        orig_sev_val = 0
        if incident.priority and incident.priority.severity:
            orig_sev_val = self.config.SEVERITY_VALUES.get(incident.priority.severity, 0)
        else:
            # Fallback if priority wasn't run
            for ev in before_ev:
                if ev.ai_severity_raw:
                    try:
                        sev_enum = SeverityLevel(ev.ai_severity_raw.lower())
                        val = self.config.SEVERITY_VALUES.get(sev_enum, 0)
                        if val > orig_sev_val:
                            orig_sev_val = val
                    except ValueError:
                        pass
        
        # Default to LOW (1) if no prior severity could be established
        if orig_sev_val == 0:
            orig_sev_val = 1

        # 3. Evaluate After Evidence
        has_valid_after = False
        outcome = VerificationResult.FULLY_RESOLVED  # Start optimistic, downgrade upon conflicting evidence

        if not after_ev:
            outcome = VerificationResult.INSUFFICIENT_EVIDENCE
            explanation = "No verification evidence submitted."
        else:
            related_count = 0
            for ev in after_ev:
                if ev.ai_ambiguity_flag:
                    continue  # Skip unusable evidence
                
                has_valid_after = True
                
                # Check for category mismatch -> implies unrelated image
                if ev.ai_category != incident.issue_type:
                    # Unrelated evidence cannot prove resolution
                    pass 
                else:
                    related_count += 1
                    # Category matches, assess severity
                    if ev.ai_severity_raw and ev.ai_severity_raw.lower() == 'none':
                        ev_sev_val = 0
                    else:
                        ev_sev_val = 1 # assume low
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

        # 5. Incident & SLA State Transitions
        if outcome == VerificationResult.FULLY_RESOLVED:
            incident.status = IncidentStatus.RESOLVED
            if incident.sla and incident.sla.state != AccountabilityState.RESOLVED:
                incident.sla.state = AccountabilityState.RESOLVED
                incident.sla.resolved_at = now

        # 6. Timeline Event
        event = IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.VERIFICATION_RESULT_SET,
            actor="system",
            summary=f"Verification completed: {outcome.value.upper()}. {explanation}",
            payload={"result": outcome.value, "confidence": record.confidence}
        )
        self.session.add(event)
        
        await self.session.commit()
        return record

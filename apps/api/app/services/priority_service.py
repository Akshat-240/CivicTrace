"""
Priority Engine service.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import EventType, PriorityLevel, SeverityLevel
from app.models.event import IncidentEvent
from app.models.incident import Incident
from app.models.priority import Priority


class PriorityConfig:
    WEIGHT_SEVERITY = 0.5
    WEIGHT_SAFETY = 0.3
    WEIGHT_PERSISTENCE = 0.2

    SEVERITY_VALUES = {
        SeverityLevel.CRITICAL: 1.0,
        SeverityLevel.HIGH: 0.75,
        SeverityLevel.MEDIUM: 0.5,
        SeverityLevel.LOW: 0.25,
    }


class PriorityService:
    """
    Computes final incident priority holistically based on evidence.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = PriorityConfig()

    async def compute_priority(self, incident_id: uuid.UUID) -> Priority:
        """
        Calculates and persists the final priority for an incident.
        """
        stmt = (
            select(Incident)
            .options(selectinload(Incident.evidence_items), selectinload(Incident.priority))
            .where(Incident.id == incident_id)
        )
        result = await self.session.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        # 1. Aggregate Evidence
        highest_severity: SeverityLevel | None = None
        highest_sev_val = 0.0
        safety_detected = False

        for ev in incident.evidence_items:
            # Aggregate Safety
            if ev.ai_safety_risk:
                safety_detected = True

            # Aggregate Severity
            if ev.ai_severity_raw:
                try:
                    sev_enum = SeverityLevel(ev.ai_severity_raw.lower())
                    val = self.config.SEVERITY_VALUES.get(sev_enum, 0.0)
                    if val > highest_sev_val:
                        highest_sev_val = val
                        highest_severity = sev_enum
                except ValueError:
                    # Ignore invalid severity strings from AI if they sneak through
                    pass

        # 2. Compute Persistence Score
        evidence_count = len(incident.evidence_items)
        days_active = abs((datetime.now(timezone.utc) - incident.created_at).total_seconds()) / 86400.0

        persistence_score = min(1.0, (evidence_count * 0.1) + (days_active / 30.0))

        # 3. Calculate Final Total Score
        safety_score = 1.0 if safety_detected else 0.0

        total_score = (
            (highest_sev_val * self.config.WEIGHT_SEVERITY) +
            (safety_score * self.config.WEIGHT_SAFETY) +
            (persistence_score * self.config.WEIGHT_PERSISTENCE)
        )

        # 4. Map to Priority Level
        if total_score >= 0.75:
            final_priority = PriorityLevel.CRITICAL
        elif total_score >= 0.50:
            final_priority = PriorityLevel.HIGH
        elif total_score >= 0.25:
            final_priority = PriorityLevel.MEDIUM
        else:
            final_priority = PriorityLevel.LOW

        # 5. Construct Explanation
        explanation = (
            f"Computed priority is {final_priority.value.upper()} (score: {total_score:.2f}). "
            f"Highest severity across {evidence_count} evidence items is {highest_severity.value.upper() if highest_severity else 'NONE'}. "
            f"Safety risk was {'DETECTED' if safety_detected else 'NOT DETECTED'}. "
            f"Persistence score is {persistence_score:.2f}."
        )

        # 6. Upsert Priority Record
        is_update = False
        priority_level_changed = False
        priority_record = incident.priority

        if priority_record:
            is_update = True
            if priority_record.final_priority != final_priority:
                priority_level_changed = True

            priority_record.severity = highest_severity
            priority_record.safety_risk = safety_detected
            priority_record.persistence_score = persistence_score
            priority_record.final_priority = final_priority
            priority_record.explanation = explanation
        else:
            priority_level_changed = True
            priority_record = Priority(
                incident_id=incident.id,
                severity=highest_severity,
                safety_risk=safety_detected,
                persistence_score=persistence_score,
                final_priority=final_priority,
                explanation=explanation
            )
            incident.priority = priority_record
            self.session.add(priority_record)

        # 7. Record Timeline Event ONLY if priority changed (or newly computed)
        if priority_level_changed:
            event_type = EventType.PRIORITY_UPDATED if is_update else EventType.PRIORITY_COMPUTED
            event = IncidentEvent(
                incident_id=incident.id,
                event_type=event_type,
                actor="system",
                summary=explanation,
                payload={
                    "total_score": total_score,
                    "severity_score": highest_sev_val,
                    "safety_score": safety_score,
                    "persistence_score": persistence_score
                }
            )
            self.session.add(event)

        await self.session.flush()
        return priority_record

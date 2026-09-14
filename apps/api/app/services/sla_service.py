"""
SLA and Accountability engine service.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import AccountabilityState, EventType, PriorityLevel, IncidentStatus
from app.models.event import IncidentEvent
from app.models.incident import Incident
from app.models.sla import SLA


class SLAConfig:
    DUE_WARNING_HOURS = 24
    ESCALATION_DELAY_HOURS = 72


class AccountabilityService:
    """
    Manages SLA tracking and accountability state machine.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = SLAConfig()

    async def start_sla(self, incident_id: uuid.UUID, current_time: Optional[datetime] = None) -> SLA:
        """
        Starts the SLA clock for an incident based on its Priority and Authority.
        """
        now = current_time or datetime.now(timezone.utc)

        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.authority),
                selectinload(Incident.priority),
                selectinload(Incident.sla),
            )
            .where(Incident.id == incident_id)
        )
        result = await self.session.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        if not incident.authority:
            raise ValueError("Cannot start SLA: No responsible Authority assigned.")

        if not incident.priority or not incident.priority.final_priority:
            raise ValueError("Cannot start SLA: Final Priority has not been computed.")

        if incident.sla:
            # SLA already running, we might update it if priority changed, but for simplicity
            # we just return the running SLA or restart it. We'll restart it for this implementation.
            pass

        # Calculate SLA duration based on Authority rules for the specific Priority
        p_level = incident.priority.final_priority
        if p_level == PriorityLevel.CRITICAL:
            hours = incident.authority.sla_hours_critical
        elif p_level == PriorityLevel.HIGH:
            hours = incident.authority.sla_hours_high
        elif p_level == PriorityLevel.MEDIUM:
            hours = incident.authority.sla_hours_medium
        else:
            hours = incident.authority.sla_hours_low

        due_at = now + timedelta(hours=hours)

        sla_record = incident.sla
        if not sla_record:
            sla_record = SLA(
                incident_id=incident.id,
                state=AccountabilityState.PENDING,
                started_at=now,
                due_at=due_at,
                is_escalation_eligible=False
            )
            incident.sla = sla_record
            self.session.add(sla_record)
        else:
            # Reset
            sla_record.state = AccountabilityState.PENDING
            sla_record.started_at = now
            sla_record.due_at = due_at
            sla_record.resolved_at = None
            sla_record.overdue_at = None
            sla_record.escalated_at = None
            sla_record.is_escalation_eligible = False

        event = IncidentEvent(
            incident_id=incident.id,
            event_type=EventType.SLA_STARTED,
            actor="system",
            summary=f"SLA clock started. {hours} hours allotted by {incident.authority.name}. Due at {due_at.isoformat()}.",
            payload={"sla_hours": hours, "due_at": due_at.isoformat()}
        )
        self.session.add(event)
        
        if incident.status == IncidentStatus.DRAFT:
            incident.status = IncidentStatus.ACTIVE
        
        await self.session.commit()
        return sla_record

    async def evaluate_sla(self, incident_id: uuid.UUID, current_time: Optional[datetime] = None) -> SLA:
        """
        Evaluates and advances the state machine for an existing SLA.
        """
        now = current_time or datetime.now(timezone.utc)

        stmt = (
            select(SLA)
            .where(SLA.incident_id == incident_id)
        )
        result = await self.session.execute(stmt)
        sla_record = result.scalar_one_or_none()

        if not sla_record:
            raise ValueError(f"SLA record for Incident {incident_id} not found.")

        if sla_record.state == AccountabilityState.RESOLVED:
            return sla_record  # Terminal state

        old_state = sla_record.state
        new_state = old_state
        note = None

        time_to_due = (sla_record.due_at - now).total_seconds() / 3600.0

        # PENDING -> DUE
        if old_state == AccountabilityState.PENDING and 0 < time_to_due <= self.config.DUE_WARNING_HOURS:
            new_state = AccountabilityState.DUE
            note = f"SLA is now DUE. Less than {self.config.DUE_WARNING_HOURS} hours remaining."

        # PENDING/DUE -> OVERDUE
        elif old_state in (AccountabilityState.PENDING, AccountabilityState.DUE) and now >= sla_record.due_at:
            new_state = AccountabilityState.OVERDUE
            sla_record.overdue_at = now
            note = "SLA deadline breached. Incident is now OVERDUE."

        # OVERDUE -> ESCALATION_ELIGIBLE
        elif old_state == AccountabilityState.OVERDUE:
            hours_overdue = (now - sla_record.due_at).total_seconds() / 3600.0
            if hours_overdue >= self.config.ESCALATION_DELAY_HOURS:
                new_state = AccountabilityState.ESCALATION_ELIGIBLE
                sla_record.escalated_at = now
                sla_record.is_escalation_eligible = True
                note = f"Incident overdue by {hours_overdue:.1f} hours. Escalation triggered."

        if new_state != old_state:
            sla_record.state = new_state
            
            event_type = EventType.ESCALATION_TRIGGERED if new_state == AccountabilityState.ESCALATION_ELIGIBLE else EventType.SLA_STATE_CHANGED
            
            event = IncidentEvent(
                incident_id=incident_id,
                event_type=event_type,
                actor="system",
                summary=note,
                payload={"previous_state": old_state.value, "new_state": new_state.value}
            )
            self.session.add(event)
            await self.session.commit()

        return sla_record

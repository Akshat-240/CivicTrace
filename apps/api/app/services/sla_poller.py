import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AccountabilityState, IncidentStatus
from app.models.incident import Incident
from app.models.sla import SLA
from app.services.sla_service import AccountabilityService

logger = logging.getLogger(__name__)

class SLAPoller:
    """
    Periodically queries active SLAs and forces evaluation.
    Handles failures per-incident so one corrupt record doesn't block the queue.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_all_active_slas(self, current_time: datetime = None) -> dict:
        """
        Finds all active SLA records and evaluates them.
        Returns a summary of processed, failed, and skipped items.
        """
        if not current_time:
            current_time = datetime.now(timezone.utc)

        # Get all incidents that are ACTIVE or UNDER_REVIEW, and have an unresolved SLA
        stmt = (
            select(Incident.id)
            .join(SLA)
            .where(Incident.status.in_([IncidentStatus.ACTIVE, IncidentStatus.UNDER_REVIEW]))
            .where(SLA.state != AccountabilityState.RESOLVED)
            .where(SLA.state != AccountabilityState.ESCALATION_ELIGIBLE) # Terminal states don't need continuous ticking
        )

        result = await self.session.execute(stmt)
        incident_ids = result.scalars().all()

        summary = {"processed": 0, "failed": 0, "total": len(incident_ids), "errors": []}

        sla_service = AccountabilityService(self.session)

        for inc_id in incident_ids:
            try:
                await sla_service.evaluate_sla(inc_id, current_time=current_time)
                summary["processed"] += 1
            except Exception as e:
                logger.error(f"Failed to evaluate SLA for incident {inc_id}: {e}")
                summary["failed"] += 1
                summary["errors"].append(str(e))
                # Rollback just in case a partial transaction was left open
                await self.session.rollback()

        return summary

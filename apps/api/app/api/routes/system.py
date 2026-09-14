from typing import Any
from fastapi import APIRouter
from app.api.dependencies import DbSession
from app.services.sla_poller import SLAPoller

router = APIRouter(prefix="/system", tags=["system"])

@router.post("/evaluate-slas", response_model=Any, summary="Manually trigger global SLA evaluation")
async def evaluate_slas(db: DbSession) -> dict:
    """
    Manually triggers the background SLA evaluation job.
    Evaluates all active incidents that are not yet resolved or escalation_eligible.
    """
    poller = SLAPoller(db)
    summary = await poller.evaluate_all_active_slas()
    return {"message": "SLA evaluation triggered", "summary": summary}

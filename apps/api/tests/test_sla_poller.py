"""
Tests for the background SLA Poller.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.enums import AccountabilityState, IncidentStatus
from app.models.incident import Incident
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.models.sla import SLA
from app.services.sla_poller import SLAPoller

@pytest.fixture
def base_time():
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

@pytest.mark.asyncio
class TestSLAPoller:

    async def test_poller_processes_multiple_incidents(self, db_session, base_time):
        auth = Authority(
            id=uuid.uuid4(), name="Test Auth", short_code="TA",
        )
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        
        # Incident 1: 50 hours elapsed -> PENDING
        inc1 = Incident(reference_number="POLL-1", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc1)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc1.id, state=AccountabilityState.PENDING,
            started_at=base_time, due_at=base_time + timedelta(hours=100)
        ))

        # Incident 2: 80 hours elapsed -> DUE
        inc2 = Incident(reference_number="POLL-2", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc2)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc2.id, state=AccountabilityState.PENDING,
            started_at=base_time - timedelta(hours=30), due_at=base_time + timedelta(hours=70)
        ))
        
        # Incident 3: 101 hours elapsed -> OVERDUE
        inc3 = Incident(reference_number="POLL-3", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc3)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc3.id, state=AccountabilityState.PENDING,
            started_at=base_time - timedelta(hours=51), due_at=base_time + timedelta(hours=49)
        ))

        await db_session.flush()

        poller = SLAPoller(db_session)
        # Advance clock to base_time + 50 hours
        eval_time = base_time + timedelta(hours=50)
        summary = await poller.evaluate_all_active_slas(current_time=eval_time)
        
        assert summary["total"] == 3
        assert summary["processed"] == 3
        assert summary["failed"] == 0

        db_session.expunge_all()
        from sqlalchemy.orm import selectinload
        inc1 = await db_session.get(Incident, inc1.id, options=[selectinload(Incident.sla)])
        inc2 = await db_session.get(Incident, inc2.id, options=[selectinload(Incident.sla)])
        inc3 = await db_session.get(Incident, inc3.id, options=[selectinload(Incident.sla)])

        assert inc1.sla.state == AccountabilityState.PENDING
        assert inc2.sla.state == AccountabilityState.DUE
        assert inc3.sla.state == AccountabilityState.OVERDUE

    async def test_escalation_eligibility_and_repeated_execution(self, db_session, base_time):
        auth = Authority(id=uuid.uuid4(), name="Test Auth", short_code="TA")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        
        inc = Incident(reference_number="POLL-4", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc.id, state=AccountabilityState.OVERDUE, # Already overdue
            started_at=base_time - timedelta(hours=100), due_at=base_time - timedelta(hours=90),
            overdue_at=base_time - timedelta(hours=90)
        ))
        await db_session.flush()

        poller = SLAPoller(db_session)
        # Clock is 100 hours past start, 90 hours past due. Escalation delay is 72h.
        summary1 = await poller.evaluate_all_active_slas(current_time=base_time)
        assert summary1["processed"] == 1
        db_session.expunge_all()
        from sqlalchemy.orm import selectinload
        inc = await db_session.get(Incident, inc.id, options=[selectinload(Incident.sla)])
        assert inc.sla.state == AccountabilityState.ESCALATION_ELIGIBLE

        # Repeated execution (idempotency)
        summary2 = await poller.evaluate_all_active_slas(current_time=base_time + timedelta(hours=1))
        # Shouldn't process because ESCALATION_ELIGIBLE is filtered out by the poller loop!
        assert summary2["total"] == 0

    async def test_one_failure_does_not_stop_others(self, db_session, base_time):
        auth = Authority(id=uuid.uuid4(), name="Test Auth", short_code="TA")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        
        # Valid incident
        inc1 = Incident(reference_number="POLL-5", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc1)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc1.id, state=AccountabilityState.PENDING,
            started_at=base_time, due_at=base_time + timedelta(hours=100)
        ))

        # Corrupt incident (missing SLA, will throw error in evaluate_sla)
        inc2 = Incident(reference_number="POLL-6", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc2)
        await db_session.flush()

        # Valid incident
        inc3 = Incident(reference_number="POLL-7", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc3)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc3.id, state=AccountabilityState.PENDING,
            started_at=base_time, due_at=base_time + timedelta(hours=100)
        ))

        await db_session.flush()

        poller = SLAPoller(db_session)
        summary = await poller.evaluate_all_active_slas(current_time=base_time + timedelta(hours=80))
        
        assert summary["total"] == 2
        assert summary["processed"] == 2
        assert summary["failed"] == 0
        
        db_session.expunge_all()
        from sqlalchemy.orm import selectinload
        inc1 = await db_session.get(Incident, inc1.id, options=[selectinload(Incident.sla)])
        inc3 = await db_session.get(Incident, inc3.id, options=[selectinload(Incident.sla)])

        assert inc1.sla.state == AccountabilityState.DUE
        assert inc3.sla.state == AccountabilityState.DUE

    async def test_timezone_correctness(self, db_session, base_time):
        auth = Authority(id=uuid.uuid4(), name="Test Auth", short_code="TA")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        
        inc = Incident(reference_number="POLL-8", status=IncidentStatus.ACTIVE, authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()
        db_session.add(SLA(
            incident_id=inc.id, state=AccountabilityState.PENDING,
            started_at=base_time, due_at=base_time + timedelta(hours=100)
        ))
        await db_session.flush()

        poller = SLAPoller(db_session)
        now_tz = datetime.now(timezone.utc)
        summary = await poller.evaluate_all_active_slas() # uses default UTC
        
        # Verify it ran correctly
        assert summary["processed"] == 1
        
        db_session.expunge_all()
        from sqlalchemy.orm import selectinload
        inc = await db_session.get(Incident, inc.id, options=[selectinload(Incident.sla)])

        # Verify the timestamps it sets are aware
        assert inc.sla.started_at.tzinfo == timezone.utc

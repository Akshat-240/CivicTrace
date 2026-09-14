"""
Tests for SLA and Accountability Engine with SLARule lookup.
"""

import uuid
import pytest
from datetime import datetime, timedelta, timezone

from app.models.authority import Authority
from app.models.enums import AccountabilityState, IncidentStatus
from app.models.incident import Incident
from app.models.jurisdiction import Jurisdiction
from app.models.sla import SLA
from app.models.sla_rule import SLARule
from app.services.sla_service import AccountabilityService


@pytest.fixture
def base_time():
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
class TestAccountabilityService:

    async def test_authority_mapping_and_deadline_calculation_with_sla_rule(self, db_session, base_time):
        auth = Authority(
            id=uuid.uuid4(), name="Test Authority", short_code="TA",
        )
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)

        # Add explicit SLA rule for pothole -> 48 hours
        rule = SLARule(
            id=uuid.uuid4(),
            authority_id=auth.id,
            issue_type="pothole",
            resolution_hours=48,
            escalation_grace_hours=72,
            is_active=True
        )
        db_session.add(rule)

        inc = Incident(
            reference_number="INC-SLA-1", status=IncidentStatus.ACTIVE, issue_type="pothole",
            created_at=base_time, authority_id=auth.id, jurisdiction_id=jur.id
        )
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time)

        assert sla.state == AccountabilityState.PENDING
        assert sla.started_at == base_time
        # Rule specifies 48 hours
        expected_due = base_time + timedelta(hours=48)
        assert sla.due_at == expected_due

    async def test_missing_authority(self, db_session, base_time):
        inc = Incident(
            reference_number="INC-SLA-2", status=IncidentStatus.ACTIVE, issue_type="pothole",
            created_at=base_time, authority_id=None
        )
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        with pytest.raises(ValueError, match="No responsible Authority assigned"):
            await svc.start_sla(inc.id, current_time=base_time)

    async def test_missing_sla_rule_handled_safely_with_fallback(self, db_session, base_time):
        # When no explicit SLA rule exists, system should fallback safely to default (72 hours)
        auth = Authority(id=uuid.uuid4(), name="Test Authority", short_code="TA_FALLBACK")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name="Test Jur", code="TJ_FALLBACK", authority_id=auth.id)
        db_session.add(jur)
        inc = Incident(
            reference_number="INC-SLA-FALLBACK", status=IncidentStatus.ACTIVE, issue_type="other_unconfigured",
            created_at=base_time, authority_id=auth.id, jurisdiction_id=jur.id
        )
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time)

        assert sla.state == AccountabilityState.PENDING
        assert sla.started_at == base_time
        # Default fallback is 72 hours
        assert sla.due_at == base_time + timedelta(hours=72)

    async def test_pending_incident(self, db_session, base_time):
        # 1. pending incident
        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=100)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-3", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time) # due in 100 hours

        # Evaluate 50 hours later
        eval_time = base_time + timedelta(hours=50)
        sla_updated = await svc.evaluate_sla(inc.id, current_time=eval_time)

        assert sla_updated.state == AccountabilityState.PENDING

    async def test_due_incident(self, db_session, base_time):
        # 2. due incident (within 24 hours of deadline)
        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T2")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=100)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-4", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time)

        # Evaluate 80 hours later (20 hours remaining)
        eval_time = base_time + timedelta(hours=80)
        sla_updated = await svc.evaluate_sla(inc.id, current_time=eval_time)

        assert sla_updated.state == AccountabilityState.DUE

    async def test_overdue_incident(self, db_session, base_time):
        # 3. overdue incident
        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T3")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=100)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-5", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time)

        # Evaluate 101 hours later
        eval_time = base_time + timedelta(hours=101)
        sla_updated = await svc.evaluate_sla(inc.id, current_time=eval_time)

        assert sla_updated.state == AccountabilityState.OVERDUE
        assert sla_updated.overdue_at == eval_time
        assert sla_updated.is_escalation_eligible == False

    async def test_escalation_eligible(self, db_session, base_time):
        # 4. escalation eligible (default > 72 hours overdue)
        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T4")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=100)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-6", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_time)

        # Manually jump to OVERDUE first
        overdue_time = base_time + timedelta(hours=101)
        await svc.evaluate_sla(inc.id, current_time=overdue_time)

        # Jump to 175 hours later (100 + 75 overdue)
        escalation_time = base_time + timedelta(hours=175)
        sla_updated = await svc.evaluate_sla(inc.id, current_time=escalation_time)

        assert sla_updated.state == AccountabilityState.ESCALATION_ELIGIBLE
        assert sla_updated.is_escalation_eligible == True
        assert sla_updated.escalated_at == escalation_time

    async def test_repeated_evaluation_determinism(self, db_session, base_time):
        # 9. repeated evaluation determinism
        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T5")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=100)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-7", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        await svc.start_sla(inc.id, current_time=base_time)

        # 80 hours -> DUE
        eval_time = base_time + timedelta(hours=80)
        s1 = await svc.evaluate_sla(inc.id, current_time=eval_time)
        assert s1.state == AccountabilityState.DUE

        # Evaluating again at 81 hours shouldn't alter state or logs incorrectly
        eval_time_2 = base_time + timedelta(hours=81)
        s2 = await svc.evaluate_sla(inc.id, current_time=eval_time_2)
        assert s2.state == AccountabilityState.DUE

    async def test_timezone_handling(self, db_session):
        # 6. timezone handling
        base_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        auth = Authority(id=uuid.uuid4(), name="Test", short_code="T6")
        db_session.add(auth)
        jur = Jurisdiction(id=uuid.uuid4(), name='J', code='J'+str(uuid.uuid4())[:8], authority_id=auth.id)
        db_session.add(jur)
        rule = SLARule(authority_id=auth.id, issue_type="pothole", resolution_hours=10)
        db_session.add(rule)
        inc = Incident(reference_number="INC-SLA-8", status=IncidentStatus.ACTIVE, issue_type="pothole", authority_id=auth.id, jurisdiction_id=jur.id)
        db_session.add(inc)
        await db_session.flush()

        svc = AccountabilityService(db_session)
        sla = await svc.start_sla(inc.id, current_time=base_utc)

        assert sla.started_at.tzinfo == timezone.utc
        assert sla.due_at.tzinfo == timezone.utc

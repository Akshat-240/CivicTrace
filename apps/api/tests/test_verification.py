"""
Tests for Resolution Verification Engine.
"""

import uuid
import pytest
from datetime import datetime, timezone

from app.models.enums import AccountabilityState, EvidenceStatus, EvidenceType, IncidentStatus, PriorityLevel, SeverityLevel, VerificationResult
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.priority import Priority
from app.models.sla import SLA
from app.services.verification_service import VerificationService


@pytest.mark.asyncio
class TestVerificationService:

    async def test_missing_after_evidence(self, db_session):
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-1", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.INSUFFICIENT_EVIDENCE
        assert inc.status == IncidentStatus.ACTIVE

    async def test_poor_after_evidence(self, db_session):
        # AI flagged it as ambiguous
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-2", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_ambiguity_flag=True
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.INSUFFICIENT_EVIDENCE
        assert inc.status == IncidentStatus.ACTIVE

    async def test_fully_resolved(self, db_session):
        # Issue is fully repaired (category matches, severity none)
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        due = now + timedelta(days=1)
        inc = Incident(reference_number="VER-3", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        sla = SLA(incident_id=inc.id, state=AccountabilityState.PENDING, due_at=due, started_at=now)
        db_session.add(sla)
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="none", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.FULLY_RESOLVED
        assert inc.status == IncidentStatus.RESOLVED
        assert inc.sla.state == AccountabilityState.RESOLVED

    async def test_partially_resolved(self, db_session):
        # Original: HIGH, After: LOW -> PARTIALLY_RESOLVED
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-4", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        pri = Priority(incident_id=inc.id, severity=SeverityLevel.HIGH)
        db_session.add(pri)
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="low", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.PARTIALLY_RESOLVED
        assert inc.status == IncidentStatus.ACTIVE

    async def test_unresolved(self, db_session):
        # Original: LOW, After: HIGH -> UNRESOLVED
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-5", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        pri = Priority(incident_id=inc.id, severity=SeverityLevel.LOW)
        db_session.add(pri)
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="high", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.UNRESOLVED

    async def test_contradictory_evidence(self, db_session):
        # Two pieces of evidence: One says FULLY_RESOLVED (no pothole), One says UNRESOLVED (high severity pothole).
        # Should degrade to UNRESOLVED safely.
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-6", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        pri = Priority(incident_id=inc.id, severity=SeverityLevel.LOW)
        db_session.add(pri)
        
        ev_after_1 = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="none", ai_ambiguity_flag=False
        )
        ev_after_2 = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="high", ai_ambiguity_flag=False
        )
        db_session.add_all([ev_after_1, ev_after_2])
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.UNRESOLVED

    async def test_repeated_verification(self, db_session):
        # Ensure idempotent upserts to VerificationRecord.
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-7", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="none", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        r1 = await svc.verify_resolution(inc.id)
        r2 = await svc.verify_resolution(inc.id)
        
        assert r1.id == r2.id
        assert r2.result == VerificationResult.FULLY_RESOLVED

    async def test_unsupported_categories(self, db_session):
        # Unrelated categories must yield INSUFFICIENT_EVIDENCE
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-8", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="SOME_BOGUS_CATEGORY", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        assert res.result == VerificationResult.INSUFFICIENT_EVIDENCE

    async def test_unrelated_bird_photo_is_insufficient(self, db_session):
        # A pothole incident with an unrelated bird photo should yield INSUFFICIENT_EVIDENCE
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-9", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()
        
        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="BIRD", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)
        
        assert res.result == VerificationResult.INSUFFICIENT_EVIDENCE

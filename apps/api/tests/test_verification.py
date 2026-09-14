"""
Tests for Resolution Verification Engine.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.enums import (
    AccountabilityState,
    EvidenceStatus,
    EvidenceType,
    IncidentStatus,
    SeverityLevel,
    VerificationResult,
)
from app.models.evidence import Evidence
from app.models.incident import Incident
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

        assert res.result == VerificationResult.NO_EVIDENCE
        assert inc.status == IncidentStatus.ACTIVE

    async def test_poor_after_evidence(self, db_session):
        # AI flagged it as ambiguous -> HUMAN_REVIEW
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-2", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_ambiguity_flag=True
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)

        assert res.result == VerificationResult.HUMAN_REVIEW
        assert inc.status == IncidentStatus.ACTIVE

    async def test_fully_resolved(self, db_session):
        # Issue is fully repaired (category matches, severity none)
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
        assert res.verified_by == "system"
        assert inc.status == IncidentStatus.ACTIVE

        inc.status = IncidentStatus.UNDER_REVIEW
        await db_session.flush()
        r2 = await svc.human_verify(
            inc.id,
            result=VerificationResult.FULLY_RESOLVED,
            explanation="Test human decision",
            verified_by="demo-authority-reviewer",
        )
        assert r2.result == VerificationResult.FULLY_RESOLVED
        assert r2.verified_by == "demo-authority-reviewer"
        assert r2.confidence == 1.0
        await db_session.refresh(inc, ["sla"])
        assert inc.status == IncidentStatus.RESOLVED
        assert inc.sla.state == AccountabilityState.RESOLVED

    async def test_not_resolved_partial_improvement(self, db_session):
        # Original: HIGH, After: LOW (still present) -> NOT_RESOLVED
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-4", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev_before = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=False, ai_category="POTHOLE", ai_severity_raw="high"
        )
        db_session.add(ev_before)
        sla = SLA(incident_id=inc.id, state=AccountabilityState.PENDING, started_at=now)
        db_session.add(sla)

        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="low", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)

        assert res.result == VerificationResult.NOT_RESOLVED
        assert inc.status == IncidentStatus.ACTIVE
        assert inc.sla.state == AccountabilityState.PENDING

    async def test_not_resolved_high_severity(self, db_session):
        # Original: LOW, After: HIGH -> NOT_RESOLVED
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-5", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev_before = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=False, ai_category="POTHOLE", ai_severity_raw="low"
        )
        db_session.add(ev_before)
        sla = SLA(incident_id=inc.id, state=AccountabilityState.PENDING, started_at=now)
        db_session.add(sla)

        ev_after = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="high", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc.id)

        assert res.result == VerificationResult.NOT_RESOLVED
        assert inc.status == IncidentStatus.ACTIVE
        assert inc.sla.state == AccountabilityState.PENDING

    async def test_contradictory_evidence(self, db_session):
        # Two pieces of evidence: One says none, One says high severity.
        # Should degrade to NOT_RESOLVED safely.
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-6", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev_before = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=False, ai_category="POTHOLE", ai_severity_raw="low"
        )
        db_session.add(ev_before)

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

        assert res.result == VerificationResult.NOT_RESOLVED

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
        # Unrelated categories must yield NO_EVIDENCE
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
        assert res.result == VerificationResult.NO_EVIDENCE

    async def test_unrelated_bird_photo_is_insufficient(self, db_session):
        # A pothole incident with an unrelated bird photo should yield NO_EVIDENCE
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

        assert res.result == VerificationResult.NO_EVIDENCE

    async def test_evidence_from_other_incident(self, db_session):
        now = datetime.now(timezone.utc)
        inc1 = Incident(reference_number="VER-10", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        inc2 = Incident(reference_number="VER-11", status=IncidentStatus.ACTIVE, issue_type="POTHOLE", created_at=now)
        db_session.add_all([inc1, inc2])
        await db_session.flush()

        # Valid verification evidence, but linked to inc2
        ev_after = Evidence(
            incident_id=inc2.id, evidence_type=EvidenceType.IMAGE, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, ai_category="POTHOLE", ai_severity_raw="none", ai_ambiguity_flag=False
        )
        db_session.add(ev_after)
        await db_session.flush()

        svc = VerificationService(db_session)
        res = await svc.verify_resolution(inc1.id)

        # inc1 has no verification evidence
        assert res.result == VerificationResult.NO_EVIDENCE

    async def test_human_verify_not_resolved_returns_to_active(self, db_session):
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-12", status=IncidentStatus.UNDER_REVIEW, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.TEXT, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, description="Attempted patch",
        )
        db_session.add(ev)
        await db_session.flush()

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.NOT_RESOLVED,
            explanation="Pothole is still present",
            verified_by="inspector-1",
        )
        assert rec.result == VerificationResult.NOT_RESOLVED
        assert inc.status == IncidentStatus.ACTIVE

    async def test_human_verify_no_evidence_returns_to_active(self, db_session):
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-13", status=IncidentStatus.UNDER_REVIEW, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.TEXT, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, description="Unusable photo",
        )
        db_session.add(ev)
        await db_session.flush()

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.NO_EVIDENCE,
            explanation="Submitted evidence is unreadable",
            verified_by="inspector-1",
        )
        assert rec.result == VerificationResult.NO_EVIDENCE
        assert inc.status == IncidentStatus.ACTIVE

    async def test_human_verify_human_review_stays_under_review(self, db_session):
        now = datetime.now(timezone.utc)
        inc = Incident(reference_number="VER-14", status=IncidentStatus.UNDER_REVIEW, issue_type="POTHOLE", created_at=now)
        db_session.add(inc)
        await db_session.flush()

        ev = Evidence(
            incident_id=inc.id, evidence_type=EvidenceType.TEXT, status=EvidenceStatus.PROCESSED,
            is_verification_evidence=True, description="Complex site repair",
        )
        db_session.add(ev)
        await db_session.flush()

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.HUMAN_REVIEW,
            explanation="Needs field audit by supervisor",
            verified_by="inspector-1",
        )
        assert rec.result == VerificationResult.HUMAN_REVIEW
        assert inc.status == IncidentStatus.UNDER_REVIEW

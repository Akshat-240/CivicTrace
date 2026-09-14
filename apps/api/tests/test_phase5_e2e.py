"""
Phase 5 End-to-End Tests.
Evidence-Backed Resolution -> Verification -> Closure.

Tests A through N verify the complete Phase 5 lifecycle.
Gate 4 regression tests (L, M) are included.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.enums import (
    AccountabilityState, EvidenceStatus, EvidenceType,
    IncidentStatus, IssueType, SeverityLevel, VerificationResult,
)
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.location import Location
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.models.priority import Priority
from app.models.sla import SLA
from app.services.incident_service import IncidentService
from app.services.verification_service import VerificationService
from app.core.errors import ConflictError


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _make_incident(db_session, status=IncidentStatus.ACTIVE, issue_type="POTHOLE"):
    loc = Location(latitude=5.0, longitude=5.0, geom="SRID=4326;POINT(5 5)")
    db_session.add(loc)
    await db_session.flush()

    inc = Incident(
        reference_number=f"P5-{uuid.uuid4().hex[:6].upper()}",
        status=status,
        issue_type=issue_type,
        title="Phase 5 test incident",
        location_id=loc.id,
        evidence_count=0,
    )
    db_session.add(inc)
    await db_session.flush()

    pri = Priority(incident_id=inc.id, severity=SeverityLevel.HIGH)
    db_session.add(pri)

    now = datetime.now(timezone.utc)
    sla = SLA(
        incident_id=inc.id,
        state=AccountabilityState.PENDING,
        started_at=now,
        due_at=now + timedelta(hours=24),
    )
    db_session.add(sla)
    await db_session.flush()
    return inc


async def _add_citizen_evidence(db_session, inc_id):
    ev = Evidence(
        incident_id=inc_id,
        evidence_type=EvidenceType.IMAGE,
        status=EvidenceStatus.PROCESSED,
        is_verification_evidence=False,
        ai_category="POTHOLE",
        ai_severity_raw="high",
        ai_ambiguity_flag=False,
        description="Citizen-submitted photo of pothole",
    )
    db_session.add(ev)
    await db_session.flush()
    return ev


async def _add_resolution_evidence(db_session, inc_id):
    ev = Evidence(
        incident_id=inc_id,
        evidence_type=EvidenceType.TEXT,
        status=EvidenceStatus.PENDING,
        is_verification_evidence=True,
        description="Road repaired: filled pothole with asphalt.",
    )
    db_session.add(ev)
    await db_session.flush()
    return ev


@pytest.mark.asyncio
class TestPhase5E2E:

    # -----------------------------------------------------------------------
    # TEST A: Resolution submission -> ACTIVE -> UNDER_REVIEW
    # -----------------------------------------------------------------------
    async def test_a_submit_resolution_transitions_to_under_review(self, db_session):
        inc = await _make_incident(db_session)
        assert inc.status == IncidentStatus.ACTIVE

        svc = VerificationService(db_session)
        ev = await svc.submit_resolution(
            incident_id=inc.id,
            description="Road has been repaired. Pothole filled and resurfaced.",
        )

        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.UNDER_REVIEW
        assert ev.is_verification_evidence is True
        assert ev.incident_id == inc.id

    # -----------------------------------------------------------------------
    # TEST B: Automatic evaluation does NOT change incident status
    # -----------------------------------------------------------------------
    async def test_b_auto_eval_does_not_change_status(self, db_session):
        inc = await _make_incident(db_session)
        await _add_citizen_evidence(db_session, inc.id)
        res_ev = await _add_resolution_evidence(db_session, inc.id)

        # Give resolution evidence PROCESSED status + matching category for FULLY_RESOLVED
        res_ev.status = EvidenceStatus.PROCESSED
        res_ev.ai_category = "POTHOLE"
        res_ev.ai_severity_raw = "none"
        res_ev.ai_ambiguity_flag = False
        await db_session.flush()

        db_session.expunge_all()
        svc = VerificationService(db_session)
        rec = await svc.verify_resolution(inc.id)

        assert rec.result == VerificationResult.FULLY_RESOLVED
        assert rec.verified_by == "system"

        # CRITICAL: Status must NOT have changed -- evaluation is advisory only.
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.ACTIVE  # Not RESOLVED -- that requires human_verify

    # -----------------------------------------------------------------------
    # TEST C: Human FULLY_RESOLVED decision -> UNDER_REVIEW -> RESOLVED
    # -----------------------------------------------------------------------
    async def test_c_human_fully_resolved_transitions_to_resolved(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        await _add_resolution_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            incident_id=inc.id,
            result=VerificationResult.FULLY_RESOLVED,
            explanation="Inspector confirmed complete repair.",
            verified_by="demo-authority-reviewer",
        )

        assert rec.result == VerificationResult.FULLY_RESOLVED
        assert rec.verified_by == "demo-authority-reviewer"
        assert rec.confidence == 1.0

        await db_session.refresh(inc, ["sla"])
        assert inc.status == IncidentStatus.RESOLVED
        assert inc.sla.state == AccountabilityState.RESOLVED

    # -----------------------------------------------------------------------
    # TEST D: Explicit close -> RESOLVED -> CLOSED
    # -----------------------------------------------------------------------
    async def test_d_explicit_close_resolved_to_closed(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.RESOLVED)

        svc = IncidentService(db_session)
        closed = await svc.close_incident(inc.id)

        assert closed.status == IncidentStatus.CLOSED

    # -----------------------------------------------------------------------
    # TEST E: Insufficient evidence -> UNDER_REVIEW -> ACTIVE (not closed)
    # -----------------------------------------------------------------------
    async def test_e_insufficient_evidence_returns_to_active(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        await _add_resolution_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            incident_id=inc.id,
            result=VerificationResult.INSUFFICIENT_EVIDENCE,
            explanation="Evidence submitted was inadequate.",
        )

        assert rec.result == VerificationResult.INSUFFICIENT_EVIDENCE
        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.ACTIVE
        assert inc.status != IncidentStatus.CLOSED

    # -----------------------------------------------------------------------
    # TEST F: Forced closure from ACTIVE/UNDER_REVIEW rejected
    # -----------------------------------------------------------------------
    async def test_f_forced_closure_from_active_rejected(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.ACTIVE)
        svc = IncidentService(db_session)

        with pytest.raises(ConflictError):
            await svc.close_incident(inc.id)

        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.ACTIVE

    async def test_f2_forced_closure_from_under_review_rejected(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        svc = IncidentService(db_session)

        with pytest.raises(ConflictError):
            await svc.close_incident(inc.id)

    # -----------------------------------------------------------------------
    # TEST G: Verification of CLOSED incident rejected
    # -----------------------------------------------------------------------
    async def test_g_verify_closed_incident_rejected(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.CLOSED)

        svc = VerificationService(db_session)
        with pytest.raises(ConflictError):
            await svc.verify_resolution(inc.id)

    async def test_g2_human_verify_closed_incident_rejected(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.CLOSED)
        await _add_resolution_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        with pytest.raises(ConflictError):
            await svc.human_verify(inc.id, result=VerificationResult.FULLY_RESOLVED)

    # -----------------------------------------------------------------------
    # TEST H: Resolution submission against CLOSED rejected
    # -----------------------------------------------------------------------
    async def test_h_submit_resolution_to_closed_rejected(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.CLOSED)

        svc = VerificationService(db_session)
        with pytest.raises(ConflictError):
            await svc.submit_resolution(inc.id, description="This should fail because incident is closed.")

        # Verify no evidence was persisted
        await db_session.refresh(inc, ["evidence_items"])
        resolution_ev = [e for e in inc.evidence_items if e.is_verification_evidence]
        assert len(resolution_ev) == 0

    # -----------------------------------------------------------------------
    # TEST I: Provenance preserved (auto eval actor="system", human actor=reviewer)
    # -----------------------------------------------------------------------
    async def test_i_provenance_preserved_auto_vs_human(self, db_session):
        inc = await _make_incident(db_session)
        res_ev = await _add_resolution_evidence(db_session, inc.id)
        res_ev.status = EvidenceStatus.PROCESSED
        res_ev.ai_category = "POTHOLE"
        res_ev.ai_severity_raw = "none"
        res_ev.ai_ambiguity_flag = False
        await db_session.flush()

        db_session.expunge_all()
        svc = VerificationService(db_session)

        # Stage 2: automatic evaluation
        auto_rec = await svc.verify_resolution(inc.id)
        assert auto_rec.verified_by == "system"
        assert auto_rec.confidence == 0.9

        # Move to UNDER_REVIEW for human step
        inc = await db_session.get(Incident, inc.id)
        inc.status = IncidentStatus.UNDER_REVIEW
        await db_session.flush()

        # Stage 3: human decision overwrites VerificationRecord
        human_rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.FULLY_RESOLVED,
            explanation="Confirmed by inspector on-site.",
            verified_by="inspector-007",
        )

        assert human_rec.id == auto_rec.id           # Same VerificationRecord
        assert human_rec.verified_by == "inspector-007"
        assert human_rec.confidence == 1.0           # Human = max confidence

    # -----------------------------------------------------------------------
    # TEST J: Idempotency -- double verify_resolution returns same record
    # -----------------------------------------------------------------------
    async def test_j_idempotency_double_auto_eval(self, db_session):
        inc = await _make_incident(db_session)
        res_ev = await _add_resolution_evidence(db_session, inc.id)
        res_ev.status = EvidenceStatus.PROCESSED
        res_ev.ai_category = "POTHOLE"
        res_ev.ai_severity_raw = "none"
        res_ev.ai_ambiguity_flag = False
        await db_session.flush()

        db_session.expunge_all()
        svc = VerificationService(db_session)
        r1 = await svc.verify_resolution(inc.id)
        r2 = await svc.verify_resolution(inc.id)

        # Same VerificationRecord (unique=True on incident_id).
        assert r1.id == r2.id
        assert r2.result == VerificationResult.FULLY_RESOLVED

    # -----------------------------------------------------------------------
    # TEST K: Citizen evidence preserved after resolution evidence submitted
    # -----------------------------------------------------------------------
    async def test_k_citizen_evidence_preserved(self, db_session):
        inc = await _make_incident(db_session)
        citizen_ev = await _add_citizen_evidence(db_session, inc.id)
        citizen_ev_id = citizen_ev.id

        svc = VerificationService(db_session)
        res_ev = await svc.submit_resolution(
            inc.id,
            description="Pothole filled with cold mix and resurfaced.",
        )

        await db_session.refresh(inc, ["evidence_items"])
        ids = [e.id for e in inc.evidence_items]
        assert citizen_ev_id in ids        # citizen evidence still there
        assert res_ev.id in ids            # resolution evidence added

        citizen_check = next(e for e in inc.evidence_items if e.id == citizen_ev_id)
        assert citizen_check.is_verification_evidence is False  # flag unchanged

        res_check = next(e for e in inc.evidence_items if e.id == res_ev.id)
        assert res_check.is_verification_evidence is True

    # -----------------------------------------------------------------------
    # TEST L: Gate 4 regression -- positive GIS
    # -----------------------------------------------------------------------
    async def test_l_gate4_regression_positive_gis(self, db_session):
        from geoalchemy2.elements import WKTElement
        from app.schemas.incident import IncidentSubmit
        from app.schemas.location import LocationCreate

        auth = Authority(
            name="Lucknow Municipal Corporation",
            short_code=f"LMC-P5-{uuid.uuid4().hex[:4]}",
            contact_email="test@lmc.up.nic.in",
            is_active=True,
        )
        db_session.add(auth)
        await db_session.flush()

        wkt = "SRID=4326;MULTIPOLYGON(((80.85 26.80, 80.92 26.80, 80.92 26.86, 80.85 26.86, 80.85 26.80)))"
        jur = Jurisdiction(
            name="Aishbagh",
            code=f"LMC-AIB-P5-{uuid.uuid4().hex[:4]}",
            authority_id=auth.id,
            boundary=WKTElement(wkt, srid=4326),
        )
        db_session.add(jur)
        await db_session.commit()

        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Gate 4 Phase 5 Regression",
            location=LocationCreate(
                latitude=26.84424505286832,
                longitude=80.88863117449993,
                accuracy_meters=10,
            ),
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "priority", "sla"])

        assert incident.jurisdiction is not None
        assert incident.authority is not None
        assert incident.authority.name == "Lucknow Municipal Corporation"
        assert incident.priority is not None
        assert incident.sla is not None

    # -----------------------------------------------------------------------
    # TEST M: Gate 4 regression -- negative GIS
    # -----------------------------------------------------------------------
    async def test_m_gate4_regression_negative_gis(self, db_session):
        from app.schemas.incident import IncidentSubmit
        from app.schemas.location import LocationCreate

        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Gate 4 Negative GIS Phase 5 Regression",
            location=LocationCreate(latitude=26.8467, longitude=80.9462, accuracy_meters=10),
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "sla"])

        assert incident.jurisdiction is None
        assert incident.authority is None
        assert incident.sla is None

    # -----------------------------------------------------------------------
    # TEST N: Cannot human-verify without resolution evidence
    # -----------------------------------------------------------------------
    async def test_n_cannot_human_verify_without_resolution_evidence(self, db_session):
        """
        An UNDER_REVIEW incident with NO resolution evidence must reject
        human_verify() -- even if the status is correct. This prevents
        bypassing the evidence requirement.
        """
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        # Deliberately add ONLY citizen evidence (is_verification_evidence=False)
        await _add_citizen_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        with pytest.raises(ConflictError) as exc_info:
            await svc.human_verify(
                inc.id,
                result=VerificationResult.FULLY_RESOLVED,
                explanation="This should be rejected.",
            )

        assert "resolution evidence" in str(exc_info.value).lower()
        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.UNDER_REVIEW  # Unchanged
        assert inc.status != IncidentStatus.RESOLVED

    # -----------------------------------------------------------------------
    # TEST N2: PARTIALLY_RESOLVED does NOT unlock RESOLVED
    # -----------------------------------------------------------------------
    async def test_n2_partially_resolved_stays_under_review(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        await _add_resolution_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.PARTIALLY_RESOLVED,
            explanation="Some work done but issue remains.",
        )

        assert rec.result == VerificationResult.PARTIALLY_RESOLVED
        await db_session.refresh(inc)
        # PARTIALLY_RESOLVED must NOT set RESOLVED or CLOSED
        assert inc.status == IncidentStatus.UNDER_REVIEW
        assert inc.status != IncidentStatus.RESOLVED
        assert inc.status != IncidentStatus.CLOSED

    # -----------------------------------------------------------------------
    # TEST: UNRESOLVED returns to ACTIVE (not UNDER_REVIEW or RESOLVED)
    # -----------------------------------------------------------------------
    async def test_unresolved_returns_to_active(self, db_session):
        inc = await _make_incident(db_session, status=IncidentStatus.UNDER_REVIEW)
        await _add_resolution_evidence(db_session, inc.id)

        svc = VerificationService(db_session)
        rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.UNRESOLVED,
            explanation="Evidence shows issue persists.",
        )

        assert rec.result == VerificationResult.UNRESOLVED
        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.ACTIVE

    # -----------------------------------------------------------------------
    # TEST: Full happy path A -> B -> C -> D
    # -----------------------------------------------------------------------
    async def test_full_happy_path(self, db_session):
        """Full lifecycle: ACTIVE -> UNDER_REVIEW -> auto-eval -> RESOLVED -> CLOSED."""
        inc = await _make_incident(db_session)
        await _add_citizen_evidence(db_session, inc.id)
        assert inc.status == IncidentStatus.ACTIVE

        svc = VerificationService(db_session)
        inc_svc = IncidentService(db_session)

        # Stage 1: submit resolution
        res_ev = await svc.submit_resolution(
            inc.id,
            description="Pothole has been filled and road resurfaced by maintenance crew.",
        )
        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.UNDER_REVIEW

        # Stage 2: automatic evaluation (advisory only)
        res_ev.status = EvidenceStatus.PROCESSED
        res_ev.ai_category = "POTHOLE"
        res_ev.ai_severity_raw = "none"
        res_ev.ai_ambiguity_flag = False
        await db_session.flush()

        db_session.expunge_all()
        auto_rec = await svc.verify_resolution(inc.id)
        assert auto_rec.result == VerificationResult.FULLY_RESOLVED
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.UNDER_REVIEW  # auto eval did NOT change status

        # Stage 3: human decision
        human_rec = await svc.human_verify(
            inc.id,
            result=VerificationResult.FULLY_RESOLVED,
            explanation="Inspector confirmed full repair.",
            verified_by="demo-authority-reviewer",
        )
        await db_session.refresh(inc)
        assert inc.status == IncidentStatus.RESOLVED
        assert human_rec.verified_by == "demo-authority-reviewer"

        # Stage 4: close
        closed_inc = await inc_svc.close_incident(inc.id)
        assert closed_inc.status == IncidentStatus.CLOSED

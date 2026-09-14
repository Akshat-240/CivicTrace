"""
Integration tests proving Incident Fusion is wired into the real incident creation path.
Covers all 7 required product scenarios.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from geoalchemy2.elements import WKTElement
from sqlalchemy import select, func

from app.models.enums import (
    AccountabilityState,
    EventType,
    EvidenceStatus,
    EvidenceType,
    IncidentStatus,
    IssueType,
)
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.models.incident import Incident
from app.models.evidence import Evidence
from app.models.location import Location
from app.models.event import IncidentEvent
from app.models.sla import SLA
from app.schemas.incident import IncidentSubmit
from app.schemas.location import LocationCreate
from app.services.incident_service import IncidentService
from app.services.fusion_service import FusionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_gis(db_session):
    """Creates a test Authority and Jurisdiction covering lat=26.84, lng=80.88."""
    auth = Authority(
        name="Lucknow Municipal Corporation",
        short_code=f"LMC-FUSION-{uuid.uuid4().hex[:4]}",
        contact_email="fusion_test@lmc.up.nic.in",
        is_active=True,
    )
    db_session.add(auth)
    await db_session.flush()

    wkt = "SRID=4326;MULTIPOLYGON(((80.80 26.80, 80.95 26.80, 80.95 26.90, 80.80 26.90, 80.80 26.80)))"
    jur = Jurisdiction(
        name="Hazratganj Ward",
        code=f"HZG-{uuid.uuid4().hex[:4]}",
        authority_id=auth.id,
        boundary=WKTElement(wkt, srid=4326),
    )
    db_session.add(jur)
    await db_session.commit()
    return auth, jur


@pytest.mark.asyncio
class TestIncidentCreationFusion:

    # -----------------------------------------------------------------------
    # Scenario 1: NEW INCIDENT (no matching candidate)
    # -----------------------------------------------------------------------
    async def test_new_incident_creation_no_match(self, db_session):
        """A new report without any nearby incidents creates a new independent incident with GIS & SLA."""
        auth, jur = await _setup_gis(db_session)
        service = IncidentService(db_session)

        data = IncidentSubmit(
            title="Pothole on Main Road",
            description="Large pothole near intersection",
            issue_type="road_damage",
            location=LocationCreate(
                latitude=26.844245,
                longitude=80.888631,
                accuracy_meters=10,
            ),
        )

        incident = await service.create_incident(data)

        assert incident is not None
        assert incident.title == "Pothole on Main Road"
        assert incident.issue_type == "road_damage"
        assert incident.evidence_count == 0
        assert incident.primary_evidence_id is None
        assert incident.jurisdiction_id == jur.id
        assert incident.authority_id == auth.id
        assert incident.sla is not None
        assert incident.sla.state == AccountabilityState.PENDING

        # Timeline includes creation, assignment, and SLA start
        timeline = await service.get_incident_timeline(incident.id)
        event_types = [e.event_type for e in timeline]
        assert EventType.INCIDENT_CREATED in event_types
        assert EventType.JURISDICTION_ASSIGNED in event_types
        assert EventType.AUTHORITY_ASSIGNED in event_types
        assert EventType.SLA_STARTED in event_types

    # -----------------------------------------------------------------------
    # Scenario 2: DUPLICATE INCIDENT (qualifying match fused into canonical)
    # -----------------------------------------------------------------------
    async def test_duplicate_incident_fused_into_canonical(self, db_session):
        """
        A second report with matching category, location within 50m, and qualifying
        time window is fused into the existing canonical incident.
        No second incident is created. Evidence, provenance, and history are preserved.
        """
        auth, jur = await _setup_gis(db_session)
        service = IncidentService(db_session)

        # 1. First citizen files a report
        data1 = IncidentSubmit(
            title="Pothole near Hazratganj",
            description="Deep pothole in middle of lane",
            issue_type="road_damage",
            location=LocationCreate(
                latitude=26.844245,
                longitude=80.888631,
                accuracy_meters=10,
            ),
        )
        inc1 = await service.create_incident(data1)
        assert inc1.evidence_count == 1

        # 2. Second citizen files a report at the exact same location with matching category
        data2 = IncidentSubmit(
            title="Dangerous crater in road",
            description="Car hit this pothole and blew a tire",
            issue_type="road_damage",
            location=LocationCreate(
                latitude=26.844245,
                longitude=80.888631,
                accuracy_meters=5,
            ),
        )
        fused_incident = await service.create_incident(data2)

        # The returned incident MUST be the canonical incident (inc1)
        assert fused_incident.id == inc1.id
        assert fused_incident.evidence_count == 2

        # Verify only 1 incident exists in DB
        incidents_stmt = select(func.count()).select_from(Incident)
        total_incidents = (await db_session.execute(incidents_stmt)).scalar()
        assert total_incidents == 1

        # Verify both evidence items are linked to canonical incident
        evidence_stmt = select(Evidence).where(Evidence.incident_id == inc1.id)
        evidence_items = (await db_session.execute(evidence_stmt)).scalars().all()
        assert len(evidence_items) == 2
        descriptions = [e.description for e in evidence_items]
        assert "Deep pothole in middle of lane" in descriptions
        assert "Car hit this pothole and blew a tire" in descriptions

        # Timeline has INCIDENT_FUSED event with score >= 0.85
        timeline = await service.get_incident_timeline(inc1.id)
        fused_events = [e for e in timeline if e.event_type == EventType.INCIDENT_FUSED]
        assert len(fused_events) == 1
        assert fused_events[0].payload["fusion_score"] >= 0.85

        # SLA count is exactly 1 (no duplicate SLA created)
        sla_stmt = select(func.count()).select_from(SLA)
        total_slas = (await db_session.execute(sla_stmt)).scalar()
        assert total_slas == 1

    # -----------------------------------------------------------------------
    # Scenario 3: NEARBY BUT DIFFERENT CATEGORY (NOT fused)
    # -----------------------------------------------------------------------
    async def test_nearby_different_category_not_fused(self, db_session):
        """Reports at the same location with incompatible categories are not fused."""
        auth, jur = await _setup_gis(db_session)
        service = IncidentService(db_session)

        # Report 1: road damage
        data1 = IncidentSubmit(
            title="Pothole",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        inc1 = await service.create_incident(data1)

        # Report 2: broken streetlight at same coordinates
        data2 = IncidentSubmit(
            title="Dark streetlight pole",
            issue_type="broken_streetlight",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        inc2 = await service.create_incident(data2)

        # Must remain two independent civic incidents
        assert inc1.id != inc2.id
        assert inc1.issue_type == "road_damage"
        assert inc2.issue_type == "broken_streetlight"

        incidents_stmt = select(func.count()).select_from(Incident)
        total_incidents = (await db_session.execute(incidents_stmt)).scalar()
        assert total_incidents == 2

    # -----------------------------------------------------------------------
    # Scenario 4: TOO FAR AWAY (NOT fused)
    # -----------------------------------------------------------------------
    async def test_too_far_away_not_fused(self, db_session):
        """Reports with matching category but >50m apart are not fused."""
        auth, jur = await _setup_gis(db_session)
        service = IncidentService(db_session)

        # Report 1
        data1 = IncidentSubmit(
            title="Pothole 1",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        inc1 = await service.create_incident(data1)

        # Report 2: ~640 meters away (0.0058 lat difference)
        data2 = IncidentSubmit(
            title="Pothole 2",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.850045, longitude=80.888631),
        )
        inc2 = await service.create_incident(data2)

        assert inc1.id != inc2.id

        incidents_stmt = select(func.count()).select_from(Incident)
        total_incidents = (await db_session.execute(incidents_stmt)).scalar()
        assert total_incidents == 2

    # -----------------------------------------------------------------------
    # Scenario 5: TOO OLD (NOT fused)
    # -----------------------------------------------------------------------
    async def test_too_old_not_fused(self, db_session):
        """Reports with matching category and location but >14 days apart are not fused."""
        auth, jur = await _setup_gis(db_session)
        service = IncidentService(db_session)

        # Create first incident and backdate created_at to 20 days ago
        data1 = IncidentSubmit(
            title="Old Pothole",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        inc1 = await service.create_incident(data1)

        now = datetime.now(timezone.utc)
        inc1.created_at = now - timedelta(days=20)
        db_session.add(inc1)
        await db_session.flush()

        # Submit new report today at same location
        data2 = IncidentSubmit(
            title="New Pothole Report",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        inc2 = await service.create_incident(data2)

        assert inc1.id != inc2.id

        incidents_stmt = select(func.count()).select_from(Incident)
        total_incidents = (await db_session.execute(incidents_stmt)).scalar()
        assert total_incidents == 2

    # -----------------------------------------------------------------------
    # Scenario 6: AMBIGUOUS EVIDENCE (NOT fused, created UNDER_REVIEW)
    # -----------------------------------------------------------------------
    async def test_ambiguous_evidence_safeguard(self, db_session):
        """Ambiguous evidence prevents auto-merging and creates an incident in UNDER_REVIEW."""
        auth, jur = await _setup_gis(db_session)
        now = datetime.now(timezone.utc)

        # Create existing active incident
        loc1 = Location(latitude=26.844245, longitude=80.888631, geom="SRID=4326;POINT(80.888631 26.844245)")
        db_session.add(loc1)
        await db_session.flush()

        inc1 = Incident(
            reference_number=f"INC-AMB-CANONICAL",
            status=IncidentStatus.ACTIVE,
            issue_type="road_damage",
            location_id=loc1.id,
            evidence_count=1,
            created_at=now,
        )
        db_session.add(inc1)
        await db_session.flush()

        # New evidence at same location marked as ambiguous
        loc2 = Location(latitude=26.844245, longitude=80.888631, geom="SRID=4326;POINT(80.888631 26.844245)")
        db_session.add(loc2)
        await db_session.flush()

        amb_ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=loc2.id,
            ai_category="road_damage",
            ai_ambiguity_flag=True,
            ai_ambiguity_reason="Photo too blurry to confirm pothole boundaries",
            occurred_at=now,
        )
        db_session.add(amb_ev)
        await db_session.flush()

        fusion_svc = FusionService(db_session)
        result_inc = await fusion_svc.fuse_evidence(amb_ev.id)

        # Must NOT merge into inc1; must be a new incident in UNDER_REVIEW
        assert result_inc.id != inc1.id
        assert result_inc.status == IncidentStatus.UNDER_REVIEW
        assert amb_ev.incident_id == result_inc.id

    # -----------------------------------------------------------------------
    # Scenario 7: DETERMINISTIC TIE-BREAKING (multiple candidates)
    # -----------------------------------------------------------------------
    async def test_deterministic_tie_breaking_multiple_candidates(self, db_session):
        """When multiple matching incidents have identical scores, deterministically selects lower UUID."""
        now = datetime.now(timezone.utc)
        same_time = now - timedelta(days=1)

        loc = Location(latitude=26.844245, longitude=80.888631, geom="SRID=4326;POINT(80.888631 26.844245)")
        db_session.add(loc)
        await db_session.flush()

        # Candidate 1
        inc1 = Incident(
            reference_number="INC-TIE-1",
            status=IncidentStatus.ACTIVE,
            issue_type="road_damage",
            location_id=loc.id,
            evidence_count=1,
            created_at=same_time,
        )
        db_session.add(inc1)

        # Candidate 2 (same score as Candidate 1)
        inc2 = Incident(
            reference_number="INC-TIE-2",
            status=IncidentStatus.ACTIVE,
            issue_type="road_damage",
            location_id=loc.id,
            evidence_count=1,
            created_at=same_time,
        )
        db_session.add(inc2)
        await db_session.flush()

        # Submit new report at same location
        service = IncidentService(db_session)
        data = IncidentSubmit(
            title="Third Pothole Report",
            issue_type="road_damage",
            location=LocationCreate(latitude=26.844245, longitude=80.888631),
        )
        fused = await service.create_incident(data)

        # Must deterministically select the one with lower UUID
        expected_inc = inc1 if str(inc1.id) < str(inc2.id) else inc2
        assert fused.id == expected_inc.id
        assert fused.evidence_count == 2

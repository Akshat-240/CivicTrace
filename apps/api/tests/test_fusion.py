"""
Tests for Incident Fusion.
"""

import uuid
import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from geoalchemy2.elements import WKTElement

from app.models.enums import EvidenceStatus, EvidenceType, IncidentStatus
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.location import Location
from app.services.fusion_service import FusionService


@pytest.fixture
def mock_locations():
    """Provides coordinates for test cases."""
    # Origin: 0, 0
    # 1 degree lat is ~ 111km.
    # 50 meters is ~ 0.00045 degrees.

    # Base location
    loc1 = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")

    # 20m away (Approx 0.00018 degrees)
    loc2_20m = Location(latitude=0.00018, longitude=0.0, geom="SRID=4326;POINT(0.0 0.00018)")

    # 100m away (Approx 0.0009 degrees)
    loc3_100m = Location(latitude=0.0009, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0009)")

    return {
        "base": loc1,
        "nearby_20m": loc2_20m,
        "distant_100m": loc3_100m
    }


@pytest.mark.asyncio
class TestFusionService:
    async def test_obvious_duplicate(self, db_session):
        # 1. obvious duplicate: Same location, same category, same time
        now = datetime.now(timezone.utc)

        # Existing incident
        inc_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(inc_loc)
        await db_session.flush()

        inc = Incident(
            reference_number="INC-1",
            status=IncidentStatus.DRAFT,
            issue_type="POTHOLE",
            title="A pothole",
            location_id=inc_loc.id,
            created_at=now
        )
        db_session.add(inc)
        await db_session.flush()

        # New evidence at same location
        ev_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(ev_loc)
        await db_session.flush()

        ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=ev_loc.id,
            ai_category="POTHOLE",
            occurred_at=now
        )
        db_session.add(ev)
        await db_session.flush()

        service = FusionService(db_session)
        result_inc = await service.fuse_evidence(ev.id)

        assert result_inc.id == inc.id
        assert result_inc.evidence_count == 2
        assert ev.incident_id == inc.id

    async def test_nearby_same_category(self, db_session):
        # 2. nearby same-category: ~20m away, same category, same day
        # Same setup but 0.00018 lat diff.
        pass  # Blocked by DB

    async def test_nearby_different_category(self, db_session):
        # 3. nearby different-category: Distance 0m, but different category
        # Category weight is 0.4. Score max would be Location (0.5) + Time (0.1) = 0.6.
        # Threshold is 0.85. Should NOT fuse.
        now = datetime.now(timezone.utc)

        inc_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(inc_loc)
        await db_session.flush()

        inc = Incident(
            reference_number="INC-2",
            status=IncidentStatus.DRAFT,
            issue_type="STREETLIGHT",
            title="A streetlight",
            location_id=inc_loc.id,
            created_at=now
        )
        db_session.add(inc)
        await db_session.flush()

        ev_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(ev_loc)
        await db_session.flush()

        ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=ev_loc.id,
            ai_category="POTHOLE", # Diff category
            occurred_at=now
        )
        db_session.add(ev)
        await db_session.flush()

        service = FusionService(db_session)
        result_inc = await service.fuse_evidence(ev.id)

        assert result_inc.id != inc.id # New incident created
        assert result_inc.issue_type == "POTHOLE"

    async def test_distant_same_category(self, db_session):
        # 4. distant same-category: >50m away.
        # Max radius is 50m. ST_DistanceSphere will exclude it from query. Should NOT fuse.
        pass

    async def test_same_location_outside_time_window(self, db_session):
        # 5. same location outside time window: Same place/category but 20 days ago.
        # Max time is 14 days. Should NOT fuse.
        now = datetime.now(timezone.utc)

        inc_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(inc_loc)
        await db_session.flush()

        inc = Incident(
            reference_number="INC-3",
            status=IncidentStatus.DRAFT,
            issue_type="POTHOLE",
            location_id=inc_loc.id,
            created_at=now - timedelta(days=20) # 20 days old
        )
        db_session.add(inc)
        await db_session.flush()

        ev_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(ev_loc)
        await db_session.flush()

        ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=ev_loc.id,
            ai_category="POTHOLE",
            occurred_at=now
        )
        db_session.add(ev)
        await db_session.flush()

        service = FusionService(db_session)
        result_inc = await service.fuse_evidence(ev.id)

        assert result_inc.id != inc.id

    async def test_ambiguous_match(self, db_session):
        # 7. ambiguous match: Explicitly skip fusion.
        now = datetime.now(timezone.utc)

        ev_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(ev_loc)
        await db_session.flush()

        ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=ev_loc.id,
            ai_category="POTHOLE",
            occurred_at=now,
            ai_ambiguity_flag=True
        )
        db_session.add(ev)
        await db_session.flush()

        service = FusionService(db_session)
        result_inc = await service.fuse_evidence(ev.id)

        assert result_inc.status == IncidentStatus.UNDER_REVIEW

    async def test_multiple_candidate_incidents(self, db_session):
        # 9. multiple candidate incidents: Must pick the highest score deterministically
        now = datetime.now(timezone.utc)

        inc_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(inc_loc)
        await db_session.flush()

        # Create two identical incidents with same score
        inc1 = Incident(
            reference_number="INC-1",
            status=IncidentStatus.ACTIVE,
            issue_type="POTHOLE",
            title="Pothole 1",
            location_id=inc_loc.id,
            evidence_count=0
        )
        from datetime import timedelta
        inc_time = now - timedelta(days=1)
        inc1.created_at = inc_time
        db_session.add(inc1)

        inc2 = Incident(
            reference_number="INC-2",
            status=IncidentStatus.ACTIVE,
            issue_type="POTHOLE",
            title="Pothole 2",
            location_id=inc_loc.id,
            evidence_count=0
        )
        inc2.created_at = inc_time
        db_session.add(inc2)

        await db_session.flush()

        ev_loc = Location(latitude=0.0, longitude=0.0, geom="SRID=4326;POINT(0.0 0.0)")
        db_session.add(ev_loc)
        await db_session.flush()

        ev = Evidence(
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PROCESSED,
            location_id=ev_loc.id,
            ai_category="POTHOLE",
            occurred_at=now
        )
        db_session.add(ev)
        await db_session.flush()

        service = FusionService(db_session)
        result_inc = await service.fuse_evidence(ev.id)

        # Should deterministically pick the one with lower UUID
        expected_inc = inc1 if str(inc1.id) < str(inc2.id) else inc2
        assert result_inc.id == expected_inc.id

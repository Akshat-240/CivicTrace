import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.incident import Incident
from app.models.authority import Authority
from app.models.enums import IncidentStatus
from app.schemas.incident import IncidentSubmit
from app.schemas.location import LocationCreate
from app.services.incident_service import IncidentService
from app.services.gis_service import GISService
from app.schemas.incident import IncidentDetail

@pytest.mark.asyncio
class TestGate4Hardening:
    async def test_a_positive_gis_path(self, db_session):
        # We need the authority and jurisdiction in the DB
        from app.models.jurisdiction import Jurisdiction
        from geoalchemy2.elements import WKTElement
        
        # Check if LMC already exists from seed, or create dummy
        auth = Authority(
            name="Lucknow Municipal Corporation",
            short_code="AUTH-LMC-TEST",
            contact_email="test@lmc.up.nic.in",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()

        wkt = "SRID=4326;MULTIPOLYGON(((80.85 26.80, 80.90 26.80, 80.90 26.85, 80.85 26.85, 80.85 26.80)))"
        jur = Jurisdiction(
            name="Aishbagh",
            code="LMC-ZONE-TEST",
            authority_id=auth.id,
            boundary=WKTElement(wkt, srid=4326)
        )
        db_session.add(jur)
        await db_session.commit()

        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Test A Positive",
            location=LocationCreate(latitude=26.84424505286832, longitude=80.88863117449993, accuracy_meters=10)
        )
        incident = await service.create_incident(data)
        
        # process workflow
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "sla"])
        
        assert incident.jurisdiction is not None
        assert incident.authority is not None
        assert incident.authority.name == "Lucknow Municipal Corporation"
        assert incident.sla is not None

    async def test_b_negative_gis_path(self, db_session):
        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Test B Negative",
            location=LocationCreate(latitude=26.8467, longitude=80.9462, accuracy_meters=10)
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "sla"])
        assert incident.jurisdiction is None
        assert incident.authority is None
        assert incident.sla is None

    async def test_c_idempotency(self, db_session):
        # We need the authority and jurisdiction in the DB
        from app.models.jurisdiction import Jurisdiction
        from geoalchemy2.elements import WKTElement
        auth = Authority(
            name="Lucknow Municipal Corporation",
            short_code="AUTH-LMC-TEST2",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()

        wkt = "SRID=4326;MULTIPOLYGON(((80.85 26.80, 80.90 26.80, 80.90 26.85, 80.85 26.85, 80.85 26.80)))"
        jur = Jurisdiction(
            name="Aishbagh",
            code="LMC-ZONE-TEST2",
            authority_id=auth.id,
            boundary=WKTElement(wkt, srid=4326)
        )
        db_session.add(jur)
        await db_session.commit()

        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Test C Idempotency",
            location=LocationCreate(latitude=26.84424505286832, longitude=80.88863117449993, accuracy_meters=10)
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "sla"])
        
        gis_service = GISService(db_session)
        result = await gis_service.resolve_jurisdiction(
            latitude=incident.location.latitude,
            longitude=incident.location.longitude,
        )
        assert result.authority_id == incident.authority_id

    async def test_d_orm_api_serialization(self, db_session):
        # We need the authority and jurisdiction in the DB
        from app.models.jurisdiction import Jurisdiction
        from geoalchemy2.elements import WKTElement
        auth = Authority(
            name="Lucknow Municipal Corporation",
            short_code="AUTH-LMC-TEST3",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()

        wkt = "SRID=4326;MULTIPOLYGON(((80.85 26.80, 80.90 26.80, 80.90 26.85, 80.85 26.85, 80.85 26.80)))"
        jur = Jurisdiction(
            name="Aishbagh",
            code="LMC-ZONE-TEST3",
            authority_id=auth.id,
            boundary=WKTElement(wkt, srid=4326)
        )
        db_session.add(jur)
        await db_session.commit()

        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Test D Serialization",
            location=LocationCreate(latitude=26.84424505286832, longitude=80.88863117449993, accuracy_meters=10)
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        await db_session.refresh(incident, ["jurisdiction", "authority", "sla"])
        
        serialized = IncidentDetail.model_validate(incident)
        assert serialized.authority is not None
        assert serialized.authority.name == "Lucknow Municipal Corporation"

        data2 = IncidentSubmit(
            issue_type="road_damage",
            title="Test D Serialization 2",
            location=LocationCreate(latitude=26.8467, longitude=80.9462, accuracy_meters=10)
        )
        incident2 = await service.create_incident(data2)
        await service.process_incident_workflow(incident2.id)
        await db_session.refresh(incident2, ["jurisdiction", "authority", "sla"])
        
        serialized2 = IncidentDetail.model_validate(incident2)
        assert serialized2.authority is None

    async def test_e_citizen_regression(self, db_session):
        service = IncidentService(db_session)
        data = IncidentSubmit(
            issue_type="road_damage",
            title="Test E Citizen Regression",
            location=LocationCreate(latitude=26.8467, longitude=80.9462, accuracy_meters=10)
        )
        incident = await service.create_incident(data)
        await service.process_incident_workflow(incident.id)
        assert incident is not None

    async def test_f_db_invariant_rejects_orphan_authority(self, db_session):
        """
        Directly prove: DB constraint rejects jurisdiction_id=NULL + authority_id=<valid>.
        The INSERT must raise an IntegrityError / CheckViolation.
        """
        import sqlalchemy.exc
        from sqlalchemy import text

        # Create a real authority to use as the orphan target
        auth = Authority(
            name="Orphan Authority Test",
            short_code="ORPHAN-TEST",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()

        # Attempt to insert an incident with authority but NO jurisdiction
        orphan = Incident(
            reference_number="INC-ORPHAN-TEST",
            status=IncidentStatus.DRAFT,
            jurisdiction_id=None,     # no GIS match
            authority_id=auth.id,     # orphan assignment — must be rejected
            evidence_count=0,
        )
        db_session.add(orphan)

        # The DB constraint must fire on flush
        with pytest.raises(Exception) as exc_info:
            await db_session.flush()

        # Confirm it was a constraint violation (CheckViolation or IntegrityError)
        error_str = str(exc_info.value).lower()
        assert (
            "ck_incidents_jurisdiction_authority_invariant" in error_str
            or "check" in error_str
            or "integrity" in error_str
        ), f"Expected a DB constraint violation, got: {exc_info.value}"

        # Roll back so other tests are not affected
        await db_session.rollback()

    async def test_g_db_invariant_allows_valid_state(self, db_session):
        """
        Prove: DB allows jurisdiction_id=<valid> + authority_id=<valid> (positive state).
        """
        from app.models.jurisdiction import Jurisdiction
        from geoalchemy2.elements import WKTElement

        auth = Authority(
            name="Valid Authority G",
            short_code="VALID-AUTH-G",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()

        wkt = "SRID=4326;MULTIPOLYGON(((80.85 26.80, 80.90 26.80, 80.90 26.85, 80.85 26.85, 80.85 26.80)))"
        jur = Jurisdiction(
            name="Valid Zone G",
            code="VALID-ZONE-G",
            authority_id=auth.id,
            boundary=WKTElement(wkt, srid=4326)
        )
        db_session.add(jur)
        await db_session.flush()

        # Insert incident with both jurisdiction + authority set — must succeed
        valid_inc = Incident(
            reference_number="INC-VALID-G-TEST",
            status=IncidentStatus.ACTIVE,
            jurisdiction_id=jur.id,   # valid GIS match
            authority_id=auth.id,     # correctly derived from jurisdiction
            evidence_count=0,
        )
        db_session.add(valid_inc)
        await db_session.flush()  # must NOT raise

        await db_session.refresh(valid_inc)
        assert valid_inc.jurisdiction_id == jur.id
        assert valid_inc.authority_id == auth.id

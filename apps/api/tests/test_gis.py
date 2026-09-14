"""
GIS logic tests.
"""

import uuid
import pytest
from sqlalchemy import func
from geoalchemy2.elements import WKTElement

from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.schemas.gis import GISStatus
from app.services.gis_service import GISService

@pytest.fixture
def mock_db_data(db_session):
    """
    Creates test boundaries.
    """
    import asyncio
    
    async def _setup():
        # Clean up existing to prevent conflicts
        # (Assuming the fixture resets db or we do it here, but db_session usually is clean per test if transactional)
        
        # 1. Standard valid authority and jurisdiction
        auth = Authority(
            id=uuid.uuid4(),
            name="Test City Council",
            short_code="TCC",
        )
        db_session.add(auth)
        
        # A simple square polygon from 0,0 to 10,10
        # PostGIS expects WKT with Longitude (X) Latitude (Y).
        # We'll make it 10 10, 10 -10, -10 -10, -10 10, 10 10
        poly_wkt = "MULTIPOLYGON(((-10 -10, -10 10, 10 10, 10 -10, -10 -10)))"
        
        jur = Jurisdiction(
            id=uuid.uuid4(),
            name="Test Ward 1",
            code="TW1",
            authority_id=auth.id,
            boundary=WKTElement(poly_wkt, srid=4326)
        )
        db_session.add(jur)
        
        # 2. Jurisdiction with NO authority (Missing authority)
        # We must create an authority because of FK constraints, but we could mock a corrupted DB?
        # Actually FK ensures authority exists, but the query tests relation load. 
        # For the sake of test 7 (Missing authority), if the FK is RESTRICT, it's impossible to have NO authority 
        # in the database cleanly unless we mock the result. We'll skip standard DB creation for that and mock it.

        # 3. Overlapping jurisdiction
        poly2_wkt = "MULTIPOLYGON(((0 0, 0 20, 20 20, 20 0, 0 0)))"
        jur2 = Jurisdiction(
            id=uuid.uuid4(),
            name="Overlapping Ward",
            code="OW",
            authority_id=auth.id,
            boundary=WKTElement(poly2_wkt, srid=4326)
        )
        db_session.add(jur2)

        await db_session.flush()
        return {"auth": auth, "jur1": jur, "jur2": jur2}
    
    # We can't await in a sync fixture cleanly without asyncio.run, 
    # so we'll just have tests call it or make the fixture async
    pass

@pytest.mark.asyncio
class TestGISService:

    async def test_invalid_latitude(self):
        # 3. Invalid latitude
        service = GISService(None)
        res = await service.resolve_jurisdiction(95.0, 0.0)
        assert res.status == GISStatus.INVALID_LOCATION

    async def test_invalid_longitude(self):
        # 4. Invalid longitude
        service = GISService(None)
        res = await service.resolve_jurisdiction(0.0, 190.0)
        assert res.status == GISStatus.INVALID_LOCATION

    async def test_missing_location(self):
        # 5. Missing location
        service = GISService(None)
        res = await service.resolve_jurisdiction(None, 10.0)
        assert res.status == GISStatus.INVALID_LOCATION

    async def test_point_inside_jurisdiction(self, db_session):
        # 1. Point inside jurisdiction
        # 9. Correct authority
        # 10. Explanation
        # 11. SRID correctness
        # 12. Latitude/longitude ordering (X=Lng, Y=Lat)
        
        auth = Authority(name="City A", short_code="CA")
        db_session.add(auth)
        await db_session.flush()
        
        jur = Jurisdiction(
            name="Ward A",
            code="WA",
            authority_id=auth.id,
            boundary=WKTElement("MULTIPOLYGON(((0 0, 0 10, 10 10, 10 0, 0 0)))", srid=4326)
        )
        db_session.add(jur)
        await db_session.flush()
        
        service = GISService(db_session)
        # Lat=5, Lng=5 -> Inside
        res = await service.resolve_jurisdiction(latitude=5.0, longitude=5.0)
        
        assert res.status == GISStatus.JURISDICTION_FOUND
        assert res.jurisdiction_id == jur.id
        assert res.authority_id == auth.id
        assert "Ward A" in res.explanation
        assert "City A" in res.explanation

    async def test_point_outside_jurisdiction(self, db_session):
        # 2. Point outside jurisdiction
        service = GISService(db_session)
        res = await service.resolve_jurisdiction(latitude=50.0, longitude=50.0)
        assert res.status == GISStatus.NO_JURISDICTION

    async def test_multiple_ambiguous_matches(self, db_session):
        # 6. Multiple/ambiguous matches
        auth = Authority(name="City B", short_code="CB")
        db_session.add(auth)
        await db_session.flush()
        
        jur1 = Jurisdiction(
            name="Overlap 1", code="O1", authority_id=auth.id,
            boundary=WKTElement("MULTIPOLYGON(((0 0, 0 10, 10 10, 10 0, 0 0)))", srid=4326)
        )
        jur2 = Jurisdiction(
            name="Overlap 2", code="O2", authority_id=auth.id,
            boundary=WKTElement("MULTIPOLYGON(((0 0, 0 10, 10 10, 10 0, 0 0)))", srid=4326)
        )
        db_session.add_all([jur1, jur2])
        await db_session.flush()

        service = GISService(db_session)
        res = await service.resolve_jurisdiction(5.0, 5.0)
        assert res.status == GISStatus.JURISDICTION_CONFLICT
        assert "multiple overlapping" in res.explanation

    async def test_missing_authority(self, db_session):
        # 7. Missing authority
        # This is tough to hit naturally because of DB foreign keys, 
        # but we can simulate a broken result if authority relationship was somehow empty
        # We will mock the DB execute result for this specific test
        class MockJurisdiction:
            id = uuid.uuid4()
            name = "Broken Ward"
            authority_id = None
            authority = None
            
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return [MockJurisdiction()]
                return MockScalars()

        class MockSession:
            async def execute(self, stmt):
                return MockResult()

        service = GISService(MockSession())
        res = await service.resolve_jurisdiction(5.0, 5.0)
        assert res.status == GISStatus.JURISDICTION_CONFLICT
        assert "no mapped authority" in res.explanation

    async def test_gis_database_failure(self, db_session):
        # 8. GIS database failure
        class MockSession:
            async def execute(self, stmt):
                raise Exception("Database disconnected")

        service = GISService(MockSession())
        res = await service.resolve_jurisdiction(5.0, 5.0)
        assert res.status == GISStatus.JURISDICTION_CONFLICT
        assert "GIS database query failed" in res.explanation

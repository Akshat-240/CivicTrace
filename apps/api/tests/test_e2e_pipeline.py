"""
End-to-End backend pipeline integration tests.
Ensures the complete lifecycle respects architectural boundaries.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.enums import EvidenceType, EvidenceStatus, AccountabilityState, IncidentStatus, VerificationResult, SeverityLevel, PriorityLevel, IssueType
from app.models.evidence import Evidence
from app.models.location import Location
from app.models.jurisdiction import Jurisdiction
from app.models.authority import Authority
from app.models.incident import Incident
from app.models.sla import SLA
from app.services.ai.service import AIService
from app.services.ai.base import AIProvider
from app.schemas.ai import AIAnalysisResult
from app.services.fusion_service import FusionService
from app.services.incident_service import IncidentService
from app.services.gis_service import GISService
from app.services.priority_service import PriorityService
from app.services.sla_service import AccountabilityService
from app.services.verification_service import VerificationService
from app.services.sla_poller import SLAPoller

class MockAIProvider(AIProvider):
    def __init__(self, result: AIAnalysisResult):
        self.result = result
        
    async def analyze_evidence(self, description, media_urls):
        return self.result

@pytest.mark.asyncio
class TestE2EPipeline:
    
    async def _setup_authority_and_jurisdiction(self, db_session):
        auth = Authority(
            id=uuid.uuid4(),
            name="Test City Council",
            short_code="TCC",
            contact_email="test@example.com",
            is_active=True
        )
        db_session.add(auth)
        await db_session.flush()
        
        # Insert a simple square polygon using PostGIS WKT
        wkt = "SRID=4326;MULTIPOLYGON(((0 0, 10 0, 10 10, 0 10, 0 0)))"
        
        jur = Jurisdiction(
            id=uuid.uuid4(),
            authority_id=auth.id,
            name="Test City Center",
            code="TCC_CENTER",
            boundary=wkt
        )
        db_session.add(jur)
        await db_session.flush()
        return auth, jur

    async def _create_evidence(self, db_session, lat, lng, is_verification=False):
        loc = Location(latitude=lat, longitude=lng, geom=f"SRID=4326;POINT({lng} {lat})")
        db_session.add(loc)
        await db_session.flush()
        
        ev = Evidence(
            location_id=loc.id,
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PENDING,
            is_verification_evidence=is_verification,
            description="A test pothole"
        )
        db_session.add(ev)
        await db_session.flush()
        return ev
    
    async def _run_ai(self, db_session, ev, category=IssueType.POTHOLE, severity=SeverityLevel.HIGH, ambiguity=False):
        ai_res = AIAnalysisResult(
            civic_issue_category=category,
            confidence=0.95,
            severity_assessment=severity,
            safety_risk_detected=True if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] else False,
            ambiguity_flag=ambiguity,
            ambiguity_reason="Unclear" if ambiguity else None,
            explanation="Test explanation"
        )
        ai = AIService(db_session, provider=MockAIProvider(ai_res))
        await ai.process_evidence(ev.id)
        await db_session.refresh(ev)
        return ev

    async def test_scenario_1_normal_civic_incident(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev, IssueType.POTHOLE, SeverityLevel.HIGH)
        # 3. Fusion
        fusion = FusionService(db_session)
        incident = await fusion.fuse_evidence(ev.id)
        assert incident.status == IncidentStatus.DRAFT
        
        # 4. GIS / Jurisdiction
        gis = IncidentService(db_session)
        await gis.assign_jurisdiction(incident.id)
        await db_session.refresh(incident)
        assert incident.jurisdiction_id == jur.id
        
        priority = PriorityService(db_session)
        await priority.compute_priority(incident.id)
        await db_session.refresh(incident, ['priority'])
        assert incident.priority.severity == SeverityLevel.HIGH
        
        sla_svc = AccountabilityService(db_session)
        await sla_svc.start_sla(incident.id)
        await db_session.refresh(incident, ['sla'])
        assert incident.sla.state == AccountabilityState.PENDING
        assert incident.sla.due_at is not None

    async def test_scenario_2_duplicate_evidence(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1)
        fusion = FusionService(db_session)
        inc1 = await fusion.fuse_evidence(ev1.id)
        
        ev2 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev2)
        inc2 = await fusion.fuse_evidence(ev2.id)
        
        assert inc1.id == inc2.id
        await db_session.refresh(inc1, ['evidence_items'])
        assert len(inc1.evidence_items) == 2

    async def test_scenario_3_gis_conflict(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev = await self._create_evidence(db_session, 20.0, 20.0)
        await self._run_ai(db_session, ev)
        
        fusion = FusionService(db_session)
        incident = await fusion.fuse_evidence(ev.id)
        
        gis = IncidentService(db_session)
        await gis.assign_jurisdiction(incident.id)
        await db_session.refresh(incident)
        assert incident.jurisdiction_id is None

    async def test_scenario_4_insufficient_evidence(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.GRAFFITI)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.INSUFFICIENT_EVIDENCE

    async def test_scenario_5_unresolved_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.MEDIUM)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.POTHOLE, SeverityLevel.HIGH)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.UNRESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.ACTIVE

    async def test_scenario_6_partial_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.POTHOLE, SeverityLevel.LOW)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.PARTIALLY_RESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.ACTIVE

    async def test_scenario_7_fully_successful_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        
        ev_after.status = EvidenceStatus.PROCESSED
        ev_after.ai_category = "pothole"
        ev_after.ai_severity_raw = "none"
        db_session.add(ev_after)
        await db_session.flush()
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.FULLY_RESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.RESOLVED

    async def test_scenario_8_sla_breach(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        await db_session.refresh(inc, ['sla'])
        jur = Jurisdiction(
            id=uuid.uuid4(),
            authority_id=auth.id,
            name="Test City Center",
            code="TCC_CENTER",
            boundary=wkt
        )
        db_session.add(jur)
        await db_session.flush()
        return auth, jur

    async def _create_evidence(self, db_session, lat, lng, is_verification=False):
        loc = Location(latitude=lat, longitude=lng, geom=f"SRID=4326;POINT({lng} {lat})")
        db_session.add(loc)
        await db_session.flush()
        
        ev = Evidence(
            location_id=loc.id,
            evidence_type=EvidenceType.IMAGE,
            status=EvidenceStatus.PENDING,
            is_verification_evidence=is_verification,
            description="A test pothole"
        )
        db_session.add(ev)
        await db_session.flush()
        return ev
    
    async def _run_ai(self, db_session, ev, category=IssueType.POTHOLE, severity=SeverityLevel.HIGH, ambiguity=False):
        ai_res = AIAnalysisResult(
            civic_issue_category=category,
            confidence=0.95,
            severity_assessment=severity,
            safety_risk_detected=True if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] else False,
            ambiguity_flag=ambiguity,
            ambiguity_reason="Unclear" if ambiguity else None,
            explanation="Test explanation"
        )
        ai = AIService(db_session, provider=MockAIProvider(ai_res))
        await ai.process_evidence(ev.id)
        await db_session.refresh(ev)
        return ev

    async def test_scenario_1_normal_civic_incident(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev, IssueType.POTHOLE, SeverityLevel.HIGH)
        # 3. Fusion
        fusion = FusionService(db_session)
        incident = await fusion.fuse_evidence(ev.id)
        assert incident.status == IncidentStatus.DRAFT
        
        # 4. GIS / Jurisdiction
        gis = IncidentService(db_session)
        await gis.assign_jurisdiction(incident.id)
        await db_session.refresh(incident)
        assert incident.jurisdiction_id == jur.id
        
        priority = PriorityService(db_session)
        await priority.compute_priority(incident.id)
        await db_session.refresh(incident, ['priority'])
        assert incident.priority.severity == SeverityLevel.HIGH
        
        sla_svc = AccountabilityService(db_session)
        await sla_svc.start_sla(incident.id)
        await db_session.refresh(incident, ['sla'])
        assert incident.sla.state == AccountabilityState.PENDING
        assert incident.sla.due_at is not None

    async def test_scenario_2_duplicate_evidence(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1)
        fusion = FusionService(db_session)
        inc1 = await fusion.fuse_evidence(ev1.id)
        
        ev2 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev2)
        inc2 = await fusion.fuse_evidence(ev2.id)
        
        assert inc1.id == inc2.id
        await db_session.refresh(inc1, ['evidence_items'])
        assert len(inc1.evidence_items) == 2

    async def test_scenario_3_gis_conflict(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        
        ev = await self._create_evidence(db_session, 20.0, 20.0)
        await self._run_ai(db_session, ev)
        
        fusion = FusionService(db_session)
        incident = await fusion.fuse_evidence(ev.id)
        
        gis = IncidentService(db_session)
        await gis.assign_jurisdiction(incident.id)
        await db_session.refresh(incident)
        assert incident.jurisdiction_id is None

    async def test_scenario_4_insufficient_evidence(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.GRAFFITI)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.INSUFFICIENT_EVIDENCE

    async def test_scenario_5_unresolved_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.MEDIUM)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.POTHOLE, SeverityLevel.HIGH)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.UNRESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.ACTIVE

    async def test_scenario_6_partial_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        await self._run_ai(db_session, ev_after, IssueType.POTHOLE, SeverityLevel.LOW)
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.PARTIALLY_RESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.ACTIVE

    async def test_scenario_7_fully_successful_repair(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        ev_after = await self._create_evidence(db_session, 5.0, 5.0, is_verification=True)
        ev_after.incident_id = inc.id
        
        ev_after.status = EvidenceStatus.PROCESSED
        ev_after.ai_category = "pothole"
        ev_after.ai_severity_raw = "none"
        db_session.add(ev_after)
        await db_session.flush()
        
        db_session.expunge_all()
        verification = VerificationService(db_session)
        rec = await verification.verify_resolution(inc.id)
        assert rec.result == VerificationResult.FULLY_RESOLVED
        
        inc = await db_session.get(Incident, inc.id)
        assert inc.status == IncidentStatus.RESOLVED

    async def test_scenario_8_sla_breach(self, db_session):
        auth, jur = await self._setup_authority_and_jurisdiction(db_session)
        ev1 = await self._create_evidence(db_session, 5.0, 5.0)
        await self._run_ai(db_session, ev1, IssueType.POTHOLE, SeverityLevel.HIGH)
        inc = await FusionService(db_session).fuse_evidence(ev1.id)
        await IncidentService(db_session).assign_jurisdiction(inc.id)
        await PriorityService(db_session).compute_priority(inc.id)
        await db_session.refresh(inc, ['authority', 'priority', 'sla']); await AccountabilityService(db_session).start_sla(inc.id)
        
        await db_session.refresh(inc, ['sla'])
        inc.sla.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        inc.sla.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.add(inc.sla)
        await db_session.commit()
        
        slas = await SLAPoller(db_session).evaluate_all_active_slas()
        
        await db_session.refresh(inc, ['sla'])
        assert inc.sla.state == AccountabilityState.OVERDUE

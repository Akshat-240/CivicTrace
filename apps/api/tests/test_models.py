"""
Tests for ORM model imports, relationships, and schema validation.

These tests do NOT require a live database — they verify:
- All models import cleanly from the package.
- Enum values are correct.
- Pydantic schemas validate valid data.
- Pydantic schemas reject invalid data with clear errors.
- ORM model metadata (table names, columns, indexes) is correct.

Database persistence tests live in test_model_persistence.py.
"""

import uuid

import pytest

from app.models import (
    Asset,
    Authority,
    Evidence,
    Incident,
    IncidentEvent,
    Jurisdiction,
    Location,
    Priority,
    SLA,
    VerificationRecord,
)
from app.models.enums import (
    AccountabilityState,
    AssetType,
    EvidenceStatus,
    EvidenceType,
    EventType,
    IncidentStatus,
    IssueType,
    PriorityLevel,
    SeverityLevel,
    VerificationResult,
)


# ---------------------------------------------------------------------------
# Import and registration
# ---------------------------------------------------------------------------


class TestModelImports:
    def test_all_models_importable(self):
        """All 10 domain models must be importable from the models package."""
        # If any import fails the test collection itself fails — this just
        # makes intent explicit.
        assert Location.__tablename__ == "locations"
        assert Authority.__tablename__ == "authorities"
        assert Jurisdiction.__tablename__ == "jurisdictions"
        assert Incident.__tablename__ == "incidents"
        assert Evidence.__tablename__ == "evidence"
        assert Asset.__tablename__ == "assets"
        assert Priority.__tablename__ == "priorities"
        assert SLA.__tablename__ == "slas"
        assert VerificationRecord.__tablename__ == "verification_records"
        assert IncidentEvent.__tablename__ == "incident_events"

    def test_all_models_have_base_columns(self):
        """Every model must have the id / created_at / updated_at columns from Base."""
        for model in (
            Location, Authority, Jurisdiction, Incident, Evidence,
            Asset, Priority, SLA, VerificationRecord, IncidentEvent,
        ):
            cols = {c.name for c in model.__table__.columns}
            assert "id" in cols, f"{model.__name__} missing 'id'"
            assert "created_at" in cols, f"{model.__name__} missing 'created_at'"
            assert "updated_at" in cols, f"{model.__name__} missing 'updated_at'"


# ---------------------------------------------------------------------------
# Enum correctness
# ---------------------------------------------------------------------------


class TestEnums:
    def test_incident_status_values(self):
        assert IncidentStatus.DRAFT == "draft"
        assert IncidentStatus.ACTIVE == "active"
        assert IncidentStatus.RESOLVED == "resolved"
        assert IncidentStatus.CLOSED == "closed"
        assert IncidentStatus.INVALID == "invalid"

    def test_evidence_type_values(self):
        assert EvidenceType.IMAGE == "image"
        assert EvidenceType.VIDEO == "video"
        assert EvidenceType.TEXT == "text"

    def test_accountability_state_ordering(self):
        """States must be present and distinct."""
        states = {
            AccountabilityState.PENDING,
            AccountabilityState.DUE,
            AccountabilityState.OVERDUE,
            AccountabilityState.ESCALATION_ELIGIBLE,
            AccountabilityState.RESOLVED,
        }
        assert len(states) == 5

    def test_verification_result_values(self):
        assert VerificationResult.FULLY_RESOLVED == "fully_resolved"
        assert VerificationResult.PARTIALLY_RESOLVED == "partially_resolved"
        assert VerificationResult.UNRESOLVED == "unresolved"
        assert VerificationResult.INSUFFICIENT_EVIDENCE == "insufficient_evidence"

    def test_priority_levels_complete(self):
        levels = {PriorityLevel.LOW, PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL}
        assert len(levels) == 4

    def test_event_type_count(self):
        """Verify all expected event types exist."""
        event_values = {e.value for e in EventType}
        assert "evidence_submitted" in event_values
        assert "incident_created" in event_values
        assert "sla_started" in event_values
        assert "verification_result_set" in event_values
        assert "escalation_triggered" in event_values


# ---------------------------------------------------------------------------
# ORM table structure
# ---------------------------------------------------------------------------


class TestTableStructure:
    def test_incident_has_required_columns(self):
        cols = {c.name for c in Incident.__table__.columns}
        required = {
            "reference_number", "status", "issue_type", "description",
            "location_id", "jurisdiction_id", "authority_id",
            "ai_confidence", "ai_ambiguity_flag", "evidence_count",
        }
        assert required.issubset(cols), f"Missing: {required - cols}"

    def test_evidence_has_ai_columns(self):
        cols = {c.name for c in Evidence.__table__.columns}
        ai_cols = {
            "ai_category", "ai_confidence", "ai_safety_risk",
            "ai_ambiguity_flag", "ai_ambiguity_reason", "ai_perception_payload",
        }
        assert ai_cols.issubset(cols)

    def test_sla_has_all_timestamps(self):
        cols = {c.name for c in SLA.__table__.columns}
        ts_cols = {"started_at", "due_at", "resolved_at", "overdue_at", "escalated_at"}
        assert ts_cols.issubset(cols)

    def test_verification_has_before_after_evidence(self):
        cols = {c.name for c in VerificationRecord.__table__.columns}
        assert "before_evidence_id" in cols
        assert "after_evidence_id" in cols
        assert "result" in cols
        assert "confidence" in cols

    def test_incident_event_has_payload(self):
        cols = {c.name for c in IncidentEvent.__table__.columns}
        assert "event_type" in cols
        assert "actor" in cols
        assert "payload" in cols

    def test_location_has_geometry_column(self):
        cols = {c.name for c in Location.__table__.columns}
        assert "geom" in cols
        assert "latitude" in cols
        assert "longitude" in cols

    def test_jurisdiction_has_boundary_column(self):
        cols = {c.name for c in Jurisdiction.__table__.columns}
        assert "boundary" in cols
        assert "authority_id" in cols

    def test_priority_is_unique_per_incident(self):
        """Priority.incident_id must have a unique constraint (enforces 1-to-1)."""
        priority_cols = {
            c.name: c for c in Priority.__table__.columns
        }
        assert priority_cols["incident_id"].unique

    def test_sla_is_unique_per_incident(self):
        """SLA.incident_id must have a unique constraint (enforces 1-to-1)."""
        sla_cols = {c.name: c for c in SLA.__table__.columns}
        assert sla_cols["incident_id"].unique


# ---------------------------------------------------------------------------
# Pydantic schema validation
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_location_create_valid(self):
        from app.schemas.location import LocationCreate
        loc = LocationCreate(latitude=34.05, longitude=-118.24)
        assert loc.latitude == 34.05
        assert loc.longitude == -118.24

    def test_location_create_rejects_invalid_lat(self):
        from pydantic import ValidationError
        from app.schemas.location import LocationCreate
        with pytest.raises(ValidationError):
            LocationCreate(latitude=200.0, longitude=0.0)

    def test_location_create_rejects_invalid_lng(self):
        from pydantic import ValidationError
        from app.schemas.location import LocationCreate
        with pytest.raises(ValidationError):
            LocationCreate(latitude=0.0, longitude=-200.0)

    def test_evidence_submit_valid(self):
        from app.schemas.evidence import EvidenceSubmit
        ev = EvidenceSubmit(
            evidence_type=EvidenceType.IMAGE,
            description="Pothole on Main St",
        )
        assert ev.evidence_type == EvidenceType.IMAGE

    def test_incident_list_item_from_orm(self):
        """IncidentListItem must accept an ORM-like dict via from_attributes."""
        from app.schemas.incident import IncidentListItem
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        item = IncidentListItem(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            reference_number="INC-2026-001",
            status=IncidentStatus.DRAFT,
            evidence_count=1,
            ai_ambiguity_flag=False,
        )
        assert item.reference_number == "INC-2026-001"
        assert item.status == IncidentStatus.DRAFT

    def test_verification_submit_requires_result(self):
        from pydantic import ValidationError
        from app.schemas.priority import VerificationSubmit
        with pytest.raises(ValidationError):
            VerificationSubmit()  # result is required

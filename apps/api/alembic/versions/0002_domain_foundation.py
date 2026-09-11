"""
Domain foundation migration: create all core CivicTrace tables.

Tables created (in dependency order):
  1. locations
  2. authorities
  3. jurisdictions
  4. incidents
  5. evidence
  6. assets
  7. priorities
  8. slas
  9. verification_records
  10. incident_events

All tables use UUID primary keys (gen_random_uuid() for DB-side generation).
String enum columns use VARCHAR with CHECK constraints instead of PostgreSQL
native ENUM types — this avoids the pain of ALTER TYPE when new states are added.

Revision ID: 0002
Revises: 0001_enable_postgis
Create Date: 2026-09-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0002_domain_foundation"
down_revision: Union[str, None] = "0001_enable_postgis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Controlled values for CHECK constraints (keeps migration self-documenting)
# ---------------------------------------------------------------------------
INCIDENT_STATUSES = (
    "draft", "active", "under_review", "resolved", "closed", "invalid"
)
ISSUE_TYPES = (
    "road_damage", "pothole", "flooding", "illegal_dumping", "graffiti",
    "broken_streetlight", "damaged_signage", "water_leak", "sewage_overflow",
    "overgrown_vegetation", "abandoned_vehicle", "noise_complaint", "other",
)
EVIDENCE_TYPES = ("image", "video", "text", "audio")
EVIDENCE_STATUSES = ("pending", "processing", "processed", "failed", "rejected")
SEVERITY_LEVELS = ("low", "medium", "high", "critical")
PRIORITY_LEVELS = ("low", "medium", "high", "critical")
ACCOUNTABILITY_STATES = (
    "pending", "due", "overdue", "escalation_eligible", "resolved"
)
VERIFICATION_RESULTS = (
    "fully_resolved", "partially_resolved", "unresolved", "insufficient_evidence"
)
ASSET_TYPES = (
    "road", "footpath", "streetlight", "signage", "drain",
    "water_main", "sewer", "park", "bridge", "other",
)
EVENT_TYPES = (
    "evidence_submitted", "evidence_processed",
    "incident_created", "incident_fused", "incident_status_changed",
    "jurisdiction_assigned", "authority_assigned",
    "priority_computed", "priority_updated",
    "sla_started", "sla_state_changed", "escalation_triggered",
    "verification_submitted", "verification_result_set",
    "note_added", "system_note",
)


def _in_list(col: str, values: tuple) -> str:
    """Generate a CHECK IN constraint string."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{col} IN ({quoted})"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. locations
    # ------------------------------------------------------------------
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        # PostGIS geometry — spatial index created separately below
        sa.Column("geom", Geometry("POINT", srid=4326, spatial_index=False), nullable=True),
        sa.Column("address_raw", sa.Text, nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("suburb", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postcode", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("accuracy_meters", sa.Float, nullable=True),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_locations_lat"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_locations_lng"),
    )
    op.create_index("ix_locations_id", "locations", ["id"])
    op.create_index("ix_locations_lat_lng", "locations", ["latitude", "longitude"])
    # PostGIS spatial index (GIST)
    op.execute(
        "CREATE INDEX ix_locations_geom ON locations USING GIST (geom)"
        " WHERE geom IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 2. authorities
    # ------------------------------------------------------------------
    op.create_table(
        "authorities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_code", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sla_hours_low", sa.Integer, nullable=False, server_default="168"),
        sa.Column("sla_hours_medium", sa.Integer, nullable=False, server_default="72"),
        sa.Column("sla_hours_high", sa.Integer, nullable=False, server_default="24"),
        sa.Column("sla_hours_critical", sa.Integer, nullable=False, server_default="4"),
        sa.CheckConstraint("sla_hours_low > 0", name="ck_authorities_sla_low"),
        sa.CheckConstraint("sla_hours_medium > 0", name="ck_authorities_sla_medium"),
        sa.CheckConstraint("sla_hours_high > 0", name="ck_authorities_sla_high"),
        sa.CheckConstraint("sla_hours_critical > 0", name="ck_authorities_sla_critical"),
    )
    op.create_index("ix_authorities_id", "authorities", ["id"])
    op.create_index("ix_authorities_name", "authorities", ["name"])
    op.create_index("ix_authorities_short_code", "authorities", ["short_code"])

    # ------------------------------------------------------------------
    # 3. jurisdictions
    # ------------------------------------------------------------------
    op.create_table(
        "jurisdictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("authority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("boundary",
                  Geometry("MULTIPOLYGON", srid=4326, spatial_index=False),
                  nullable=True),
        sa.ForeignKeyConstraint(
            ["authority_id"], ["authorities.id"],
            name="fk_jurisdictions_authority_id",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_jurisdictions_id", "jurisdictions", ["id"])
    op.create_index("ix_jurisdictions_name", "jurisdictions", ["name"])
    op.create_index("ix_jurisdictions_code", "jurisdictions", ["code"])
    op.create_index("ix_jurisdictions_authority_id", "jurisdictions", ["authority_id"])
    op.execute(
        "CREATE INDEX ix_jurisdictions_boundary ON jurisdictions USING GIST (boundary)"
        " WHERE boundary IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 4. incidents
    # ------------------------------------------------------------------
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("reference_number", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("issue_type", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("authority_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_category", sa.String(100), nullable=True),
        sa.Column("ai_confidence", sa.Float, nullable=True),
        sa.Column("ai_perception_payload", postgresql.JSONB, nullable=True),
        sa.Column("ai_ambiguity_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("primary_evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("fusion_metadata", postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"], ["locations.id"],
            name="fk_incidents_location_id", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["jurisdiction_id"], ["jurisdictions.id"],
            name="fk_incidents_jurisdiction_id", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["authority_id"], ["authorities.id"],
            name="fk_incidents_authority_id", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            _in_list("status", INCIDENT_STATUSES),
            name="ck_incidents_status"
        ),
        sa.CheckConstraint(
            f"issue_type IS NULL OR {_in_list('issue_type', ISSUE_TYPES)}",
            name="ck_incidents_issue_type"
        ),
        sa.CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="ck_incidents_ai_confidence"
        ),
        sa.CheckConstraint("evidence_count >= 0", name="ck_incidents_evidence_count"),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"])
    op.create_index("ix_incidents_reference_number", "incidents", ["reference_number"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_issue_type", "incidents", ["issue_type"])
    op.create_index("ix_incidents_location_id", "incidents", ["location_id"])
    op.create_index("ix_incidents_jurisdiction_id", "incidents", ["jurisdiction_id"])
    op.create_index("ix_incidents_authority_id", "incidents", ["authority_id"])
    op.create_index("ix_incidents_status_created_at", "incidents", ["status", "created_at"])
    op.create_index("ix_incidents_issue_type_status", "incidents", ["issue_type", "status"])
    op.create_index("ix_incidents_jurisdiction_status", "incidents", ["jurisdiction_id", "status"])
    op.create_index("ix_incidents_authority_status", "incidents", ["authority_id", "status"])

    # ------------------------------------------------------------------
    # 5. evidence
    # ------------------------------------------------------------------
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("evidence_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("storage_key", sa.String(1000), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_category", sa.String(100), nullable=True),
        sa.Column("ai_confidence", sa.Float, nullable=True),
        sa.Column("ai_severity_raw", sa.String(50), nullable=True),
        sa.Column("ai_safety_risk", sa.Boolean, nullable=True),
        sa.Column("ai_perception_payload", postgresql.JSONB, nullable=True),
        sa.Column("ai_ambiguity_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ai_ambiguity_reason", sa.Text, nullable=True),
        sa.Column("is_verification_evidence", sa.Boolean, nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_evidence_incident_id", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["locations.id"],
            name="fk_evidence_location_id", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            _in_list("evidence_type", EVIDENCE_TYPES),
            name="ck_evidence_type"
        ),
        sa.CheckConstraint(
            _in_list("status", EVIDENCE_STATUSES),
            name="ck_evidence_status"
        ),
        sa.CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="ck_evidence_ai_confidence"
        ),
        sa.CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes > 0",
            name="ck_evidence_file_size"
        ),
    )
    op.create_index("ix_evidence_id", "evidence", ["id"])
    op.create_index("ix_evidence_incident_id", "evidence", ["incident_id"])
    op.create_index("ix_evidence_location_id", "evidence", ["location_id"])
    op.create_index("ix_evidence_evidence_type", "evidence", ["evidence_type"])
    op.create_index("ix_evidence_status", "evidence", ["status"])
    op.create_index("ix_evidence_status_created_at", "evidence", ["status", "created_at"])
    op.create_index("ix_evidence_incident_type", "evidence", ["incident_id", "evidence_type"])

    # ------------------------------------------------------------------
    # 6. assets
    # ------------------------------------------------------------------
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("external_asset_id", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_assets_incident_id", ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            _in_list("asset_type", ASSET_TYPES),
            name="ck_assets_type"
        ),
    )
    op.create_index("ix_assets_id", "assets", ["id"])
    op.create_index("ix_assets_incident_id", "assets", ["incident_id"])
    op.create_index("ix_assets_asset_type", "assets", ["asset_type"])
    op.create_index("ix_assets_incident_type", "assets", ["incident_id", "asset_type"])

    # ------------------------------------------------------------------
    # 7. priorities
    # ------------------------------------------------------------------
    op.create_table(
        "priorities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("safety_risk", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("persistence_score", sa.Float, nullable=True),
        sa.Column("final_priority", sa.String(20), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_priorities_incident_id", ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            f"severity IS NULL OR {_in_list('severity', SEVERITY_LEVELS)}",
            name="ck_priorities_severity"
        ),
        sa.CheckConstraint(
            f"final_priority IS NULL OR {_in_list('final_priority', PRIORITY_LEVELS)}",
            name="ck_priorities_final_priority"
        ),
        sa.CheckConstraint(
            "persistence_score IS NULL OR (persistence_score >= 0 AND persistence_score <= 1)",
            name="ck_priorities_persistence_score"
        ),
    )
    op.create_index("ix_priorities_id", "priorities", ["id"])
    op.create_index("ix_priorities_incident_id", "priorities", ["incident_id"])
    op.create_index("ix_priorities_final_priority", "priorities", ["final_priority"])

    # ------------------------------------------------------------------
    # 8. slas
    # ------------------------------------------------------------------
    op.create_table(
        "slas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("state", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overdue_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_escalation_eligible", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("escalation_note", sa.Text, nullable=True),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_slas_incident_id", ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            _in_list("state", ACCOUNTABILITY_STATES),
            name="ck_slas_state"
        ),
        sa.CheckConstraint(
            "due_at IS NULL OR started_at IS NULL OR due_at > started_at",
            name="ck_slas_due_after_start"
        ),
        sa.CheckConstraint(
            "resolved_at IS NULL OR started_at IS NULL OR resolved_at >= started_at",
            name="ck_slas_resolved_after_start"
        ),
    )
    op.create_index("ix_slas_id", "slas", ["id"])
    op.create_index("ix_slas_incident_id", "slas", ["incident_id"])
    op.create_index("ix_slas_state", "slas", ["state"])
    op.create_index("ix_slas_is_escalation_eligible", "slas", ["is_escalation_eligible"])
    op.create_index("ix_slas_state_due_at", "slas", ["state", "due_at"])

    # ------------------------------------------------------------------
    # 9. verification_records
    # ------------------------------------------------------------------
    op.create_table(
        "verification_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("before_evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("after_evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(30), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("verified_by", sa.String(50), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_verification_incident_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["before_evidence_id"], ["evidence.id"],
            name="fk_verification_before_evidence", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["after_evidence_id"], ["evidence.id"],
            name="fk_verification_after_evidence", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            f"result IS NULL OR {_in_list('result', VERIFICATION_RESULTS)}",
            name="ck_verification_result"
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_verification_confidence"
        ),
    )
    op.create_index("ix_verification_records_id", "verification_records", ["id"])
    op.create_index("ix_verification_records_incident_id", "verification_records", ["incident_id"])
    op.create_index("ix_verification_records_result", "verification_records", ["result"])

    # ------------------------------------------------------------------
    # 10. incident_events
    # ------------------------------------------------------------------
    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("actor", sa.String(200), nullable=False, server_default="system"),
        sa.Column("summary", sa.String(500), nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"],
            name="fk_incident_events_incident_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            _in_list("event_type", EVENT_TYPES),
            name="ck_incident_events_event_type"
        ),
    )
    op.create_index("ix_incident_events_id", "incident_events", ["id"])
    op.create_index("ix_incident_events_incident_id", "incident_events", ["incident_id"])
    op.create_index("ix_incident_events_event_type", "incident_events", ["event_type"])
    op.create_index(
        "ix_incident_events_incident_created",
        "incident_events", ["incident_id", "created_at"]
    )
    op.create_index(
        "ix_incident_events_type_created",
        "incident_events", ["event_type", "created_at"]
    )

    # ------------------------------------------------------------------
    # updated_at auto-update trigger (applies to all tables)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in [
        "locations", "authorities", "jurisdictions", "incidents",
        "evidence", "assets", "priorities", "slas",
        "verification_records", "incident_events",
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers first
    for table in [
        "incident_events", "verification_records", "slas", "priorities",
        "assets", "evidence", "incidents", "jurisdictions",
        "authorities", "locations",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    op.drop_table("incident_events")
    op.drop_table("verification_records")
    op.drop_table("slas")
    op.drop_table("priorities")
    op.drop_table("assets")
    op.drop_table("evidence")
    op.drop_table("incidents")
    op.drop_table("jurisdictions")
    op.drop_table("authorities")
    op.drop_table("locations")

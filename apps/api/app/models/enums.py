"""
Domain enums — controlled vocabulary for all state machines and type fields.

All enums use string values so they serialise cleanly to/from JSON and
PostgreSQL native enum types without needing numeric mappings.

Rules:
- Do NOT add business logic here. Enums are pure data.
- Add new states at the END of a class to avoid breaking existing DB rows.
- A PostgreSQL native ENUM type is created per class via SQLAlchemy's
  PgEnum; the migration will CREATE TYPE … AS ENUM.
"""

import enum


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------


class IncidentStatus(str, enum.Enum):
    """Lifecycle state of a fused incident."""

    DRAFT = "draft"                        # Evidence received, perception pending
    ACTIVE = "active"                      # Confirmed, assigned, SLA running
    UNDER_REVIEW = "under_review"          # Authority acknowledged, investigating
    RESOLVED = "resolved"                  # Verification confirmed resolution
    CLOSED = "closed"                      # Final state — no further action
    INVALID = "invalid"                    # Rejected (duplicate, out-of-scope, etc.)


class IssueType(str, enum.Enum):
    """Top-level classification of the civic issue."""

    ROAD_DAMAGE = "road_damage"
    POTHOLE = "pothole"
    FLOODING = "flooding"
    ILLEGAL_DUMPING = "illegal_dumping"
    GRAFFITI = "graffiti"
    BROKEN_STREETLIGHT = "broken_streetlight"
    DAMAGED_SIGNAGE = "damaged_signage"
    WATER_LEAK = "water_leak"
    SEWAGE_OVERFLOW = "sewage_overflow"
    OVERGROWN_VEGETATION = "overgrown_vegetation"
    ABANDONED_VEHICLE = "abandoned_vehicle"
    NOISE_COMPLAINT = "noise_complaint"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class EvidenceType(str, enum.Enum):
    """Raw media type of a single piece of evidence."""

    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    AUDIO = "audio"


class EvidenceStatus(str, enum.Enum):
    """Processing state of an evidence item."""

    PENDING = "pending"              # Uploaded, awaiting AI perception
    PROCESSING = "processing"       # AI perception in-flight
    PROCESSED = "processed"         # Perception complete, fields populated
    FAILED = "failed"               # Perception failed; manual review needed
    REJECTED = "rejected"           # Evidence discarded (e.g. unrelated content)


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------


class SeverityLevel(str, enum.Enum):
    """How severe is the physical damage or disruption."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Accountability / SLA
# ---------------------------------------------------------------------------


class AccountabilityState(str, enum.Enum):
    """
    Linear progression of SLA accountability.

    Transitions: PENDING → DUE → OVERDUE → ESCALATION_ELIGIBLE
    Closed incidents can also end in RESOLVED (terminal).
    """

    PENDING = "pending"                        # SLA clock running, within window
    DUE = "due"                                # Approaching due date
    OVERDUE = "overdue"                        # Past due date, not resolved
    ESCALATION_ELIGIBLE = "escalation_eligible"  # Overdue long enough to escalate
    RESOLVED = "resolved"                      # Closed within SLA — terminal


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class VerificationResult(str, enum.Enum):
    """Outcome of resolution verification."""

    FULLY_RESOLVED = "fully_resolved"
    NOT_RESOLVED = "not_resolved"
    NO_EVIDENCE = "no_evidence"
    HUMAN_REVIEW = "human_review"


# ---------------------------------------------------------------------------
# Incident Event
# ---------------------------------------------------------------------------


class EventType(str, enum.Enum):
    """
    Type of entry in the append-only incident timeline.

    Grouped by domain so the timeline is readable at a glance.
    """

    # Evidence
    EVIDENCE_SUBMITTED = "evidence_submitted"
    EVIDENCE_PROCESSED = "evidence_processed"

    # Incident lifecycle
    INCIDENT_CREATED = "incident_created"
    INCIDENT_FUSED = "incident_fused"          # Evidence merged into existing incident
    INCIDENT_STATUS_CHANGED = "incident_status_changed"

    # Assignment
    JURISDICTION_ASSIGNED = "jurisdiction_assigned"
    AUTHORITY_ASSIGNED = "authority_assigned"

    # SLA / Accountability
    SLA_STARTED = "sla_started"
    SLA_STATE_CHANGED = "sla_state_changed"
    ESCALATION_TRIGGERED = "escalation_triggered"

    # Verification
    VERIFICATION_SUBMITTED = "verification_submitted"
    VERIFICATION_RESULT_SET = "verification_result_set"

    # Notes
    NOTE_ADDED = "note_added"
    SYSTEM_NOTE = "system_note"


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    """User roles for authorization."""

    CITIZEN = "citizen"
    AUTHORITY = "authority"
    ADMIN = "admin"
    FIELD_WORKER = "field_worker"

class AssetType(str, enum.Enum):
    """Infrastructure asset associated with an incident."""

    ROAD = "road"
    FOOTPATH = "footpath"
    STREETLIGHT = "streetlight"
    SIGNAGE = "signage"
    DRAIN = "drain"
    WATER_MAIN = "water_main"
    SEWER = "sewer"
    PARK = "park"
    BRIDGE = "bridge"
    OTHER = "other"



class WorkerTaskStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    ON_THE_WAY = "ON_THE_WAY"
    AT_LOCATION = "AT_LOCATION"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class EvidencePhase(str, enum.Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"

"""
Models package.

Import ALL ORM models here so that:
1. Alembic `autogenerate` can discover the full schema.
2. SQLAlchemy's relationship resolution works (all mappers registered).
3. Any code that does `from app.models import Incident` works cleanly.

Add new models to this file as they are created.
"""

from app.models.enums import (  # noqa: F401
    AccountabilityState,
    AssetType,
    EvidenceStatus,
    EvidenceType,
    EventType,
    IncidentStatus,
    IssueType,
    SeverityLevel,
    VerificationResult,
    UserRole,
)
from app.models.location import Location  # noqa: F401
from app.models.authority import Authority  # noqa: F401
from app.models.jurisdiction import Jurisdiction  # noqa: F401
from app.models.incident import Incident  # noqa: F401
from app.models.evidence import Evidence  # noqa: F401
from app.models.asset import Asset  # noqa: F401
from app.models.sla import SLA  # noqa: F401
from app.models.sla_rule import SLARule  # noqa: F401
from app.models.verification import VerificationRecord
from app.models.worker_profile import WorkerProfile  # noqa: F401
from app.models.event import IncidentEvent  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    # Enums
    "AccountabilityState",
    "AssetType",
    "EvidenceStatus",
    "EvidenceType",
    "EventType",
    "IncidentStatus",
    "IssueType",
    "SeverityLevel",
    "VerificationResult",
    "UserRole",
    # Models
    "Location",
    "Authority",
    "Jurisdiction",
    "Incident",
    "Evidence",
    "Asset",
    "SLA",
    "SLARule",
    "VerificationRecord",
    "WorkerProfile",
    "IncidentEvent",
    "User",
]


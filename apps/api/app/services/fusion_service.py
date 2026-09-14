"""
Deterministic Incident Fusion Service.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import EventType, EvidenceStatus, IncidentStatus
from app.models.event import IncidentEvent
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.location import Location


class FusionConfig:
    MAX_RADIUS_METERS = 50.0
    MAX_TIME_DAYS = 14.0
    WEIGHT_LOCATION = 0.5
    WEIGHT_CATEGORY = 0.4
    WEIGHT_TIME = 0.1
    MATCH_THRESHOLD = 0.85


class FusionService:
    """
    Groups new Evidence into existing Incidents or creates new ones.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = FusionConfig()

    async def fuse_evidence(
        self,
        evidence_id: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Incident:
        """
        Determines if the evidence belongs to an existing incident.
        Returns the (merged or new) Incident.
        """
        stmt = (
            select(Evidence)
            .options(selectinload(Evidence.location))
            .where(Evidence.id == evidence_id)
        )
        result = await self.session.execute(stmt)
        evidence = result.scalar_one_or_none()

        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found.")

        if evidence.status != EvidenceStatus.PROCESSED:
            raise ValueError(f"Evidence {evidence_id} must be PROCESSED before fusion.")

        # If ambiguous, skip fusion and create explicitly for review
        if evidence.ai_ambiguity_flag:
            return await self._create_new_incident(
                evidence, 
                status=IncidentStatus.UNDER_REVIEW,
                reason="Evidence was flagged as ambiguous by AI.",
                title=title,
                description=description,
            )
            
        if not evidence.location:
            return await self._create_new_incident(
                evidence,
                status=IncidentStatus.DRAFT,
                reason="No location provided for spatial fusion.",
                title=title,
                description=description,
            )

        candidate = await self._find_best_match(evidence)

        if candidate:
            return await self._merge_into_incident(evidence, candidate)
        else:
            return await self._create_new_incident(
                evidence,
                status=IncidentStatus.DRAFT,
                reason="No matching candidate met fusion threshold.",
                title=title,
                description=description,
            )

    async def _find_best_match(self, evidence: Evidence) -> Optional[tuple[Incident, float]]:
        """
        Finds the highest scoring active incident. Returns (Incident, Score).
        """
        ev_loc = evidence.location
        now = datetime.now(timezone.utc)
        ev_time = evidence.occurred_at or evidence.created_at

        # We construct a spatial query to find active incidents within MAX_RADIUS_METERS
        # Status must be DRAFT, ACTIVE, or UNDER_REVIEW. We do not fuse into RESOLVED/CLOSED.
        active_statuses = [
            IncidentStatus.DRAFT,
            IncidentStatus.ACTIVE,
            IncidentStatus.UNDER_REVIEW
        ]

        # Create a PostGIS point from the evidence location for the spatial query
        point = func.ST_SetSRID(func.ST_MakePoint(ev_loc.longitude, ev_loc.latitude), 4326)

        # Use ST_DistanceSphere which returns distance in meters
        distance_col = func.ST_DistanceSphere(Location.geom, point).label("distance")
        
        stmt = (
            select(
                Incident,
                distance_col,
            )
            .join(Location, Incident.location_id == Location.id)
            .where(Incident.status.in_([
                IncidentStatus.DRAFT,
                IncidentStatus.ACTIVE,
                IncidentStatus.UNDER_REVIEW
            ]))
            .where(func.ST_DistanceSphere(Location.geom, point) <= self.config.MAX_RADIUS_METERS)
        )
        
        result = await self.session.execute(stmt)
        candidates = result.all()

        best_score = 0.0
        best_candidate = None

        def _norm_cat(val):
            if val is None:
                return ""
            if hasattr(val, "value"):
                return str(val.value).lower().strip()
            return str(val).lower().strip()

        ev_cat_norm = _norm_cat(evidence.ai_category)

        for inc, dist in candidates:
            # Time difference in days
            inc_time = inc.created_at
            days_diff = abs((ev_time - inc_time).total_seconds()) / 86400.0

            if days_diff > self.config.MAX_TIME_DAYS:
                continue

            # Calculate deterministic scores
            loc_score = max(0.0, 1.0 - (dist / self.config.MAX_RADIUS_METERS))
            inc_cat_norm = _norm_cat(inc.issue_type)
            cat_score = 1.0 if (inc_cat_norm and inc_cat_norm == ev_cat_norm) else 0.0
            time_score = max(0.0, 1.0 - (days_diff / self.config.MAX_TIME_DAYS))

            total_score = (
                (loc_score * self.config.WEIGHT_LOCATION) +
                (cat_score * self.config.WEIGHT_CATEGORY) +
                (time_score * self.config.WEIGHT_TIME)
            )

            if total_score >= self.config.MATCH_THRESHOLD:
                if total_score > best_score:
                    best_score = total_score
                    best_candidate = inc
                elif total_score == best_score and best_candidate is not None:
                    # Deterministic tie-breaking: prefer older incident, then lower UUID
                    if inc.created_at < best_candidate.created_at:
                        best_candidate = inc
                    elif inc.created_at == best_candidate.created_at and str(inc.id) < str(best_candidate.id):
                        best_candidate = inc

        if best_candidate:
            return (best_candidate, best_score)
        return None

    async def _merge_into_incident(self, evidence: Evidence, match: tuple[Incident, float]) -> Incident:
        inc, score = match
        
        evidence.incident_id = inc.id
        inc.evidence_count += 1
        
        event = IncidentEvent(
            incident_id=inc.id,
            event_type=EventType.INCIDENT_FUSED,
            actor="system",
            summary=f"Fused evidence {evidence.id} with score {score:.2f} >= {self.config.MATCH_THRESHOLD}",
            payload={"fusion_score": score}
        )
        self.session.add(event)
        await self.session.flush()
        return inc

    async def _create_new_incident(
        self,
        evidence: Evidence,
        status: IncidentStatus,
        reason: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Incident:
        new_inc = Incident(
            reference_number=f"INC-{uuid.uuid4().hex[:8].upper()}",
            status=status,
            issue_type=evidence.ai_category if evidence.ai_category else None,
            title=title or (f"Report of {evidence.ai_category}" if evidence.ai_category else "Civic Incident Report"),
            description=description or evidence.description,
            location_id=evidence.location_id,
            evidence_count=1,
            primary_evidence_id=evidence.id,
            ai_ambiguity_flag=evidence.ai_ambiguity_flag,
        )
        self.session.add(new_inc)
        await self.session.flush()
        
        evidence.incident_id = new_inc.id

        event = IncidentEvent(
            incident_id=new_inc.id,
            event_type=EventType.INCIDENT_CREATED,
            actor="system",
            summary=f"Created new incident. Reason: {reason}"
        )
        self.session.add(event)
        
        await self.session.flush()
        return new_inc

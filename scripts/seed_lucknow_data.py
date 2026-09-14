#!/usr/bin/env python3
"""
seed_lucknow_data.py
====================
Controlled, deterministic development-data seeder for CivicTrace.

Reads validated Lucknow data from origin/civictrace-data (without merging it)
and inserts it into the local PostgreSQL + PostGIS database.

Rules:
- Deterministic: UUIDs derived from source string IDs via uuid5.
- Idempotent:    Safe to re-run; existing rows are skipped, not overwritten.
- Transactional: All inserts happen inside a single transaction; any failure
                 triggers a full rollback so the DB is never left in a
                 partial state.
- Read-only wrt branches: reads files via `git show origin/civictrace-data:`
  so it never modifies or merges any branch.

Seed order (respects FK dependency chain):
  1. Authorities
  2. Jurisdictions (zones then wards)
  3. Locations + Incidents
  4. Assets (linked to incidents)
  5. Evidence + VerificationRecords

Excluded (benchmark/analysis files -- not for DB):
  - duplicate_cases.csv
  - authority_conflicts.csv
  - lucknow_authority_lexicon_master.csv

Usage:
  # From project root
  $env:PYTHONPATH="apps/api"
  python scripts/seed_lucknow_data.py
  python scripts/seed_lucknow_data.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap -- allow running from project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
API_PATH = ROOT / "apps" / "api"
sys.path.insert(0, str(API_PATH))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from geoalchemy2.shape import from_shape
from geoalchemy2.elements import WKTElement
from shapely.geometry import shape

from app.core.config import get_settings
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.models.location import Location
from app.models.incident import Incident
from app.models.asset import Asset
from app.models.evidence import Evidence
from app.models.verification import VerificationRecord
from app.models.event import IncidentEvent
from app.models.enums import (
    IncidentStatus,
    IssueType,
    EvidenceType,
    EvidenceStatus,
    AssetType,
    VerificationResult,
    EventType,
)

# ---------------------------------------------------------------------------
# Counters -- printed at the end
# ---------------------------------------------------------------------------
COUNTS: dict[str, dict[str, int]] = {}


def _counter(name: str) -> dict[str, int]:
    if name not in COUNTS:
        COUNTS[name] = {"inserted": 0, "existing": 0, "skipped": 0}
    return COUNTS[name]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
BRANCH = "origin/civictrace-data"


def read_source_file(rel_path: str) -> str:
    """Read a file from origin/civictrace-data without merging the branch."""
    p = ROOT / rel_path
    if p.exists():
        return p.read_text(encoding="utf-8")
    return subprocess.check_output(
        ["git", "show", f"{BRANCH}:{rel_path}"],
        cwd=str(ROOT),
    ).decode("utf-8")


def parse_csv(content: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content)))


def det_uuid(source_id: str) -> uuid.UUID:
    """Deterministic UUID from a source string ID."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, source_id)


def parse_dt(s: str) -> datetime | None:
    if not s or s.strip() == "":
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_float(s: str) -> float | None:
    try:
        v = float(s)
        # Treat 0.0 coordinates as missing (not a real location)
        return v if v != 0.0 else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Enum mapping helpers
# ---------------------------------------------------------------------------
ISSUE_TYPE_MAP: dict[str, IssueType] = {
    "POTHOLE": IssueType.POTHOLE,
    "ROAD_DAMAGE": IssueType.ROAD_DAMAGE,
    "ILLEGAL_DUMPING": IssueType.ILLEGAL_DUMPING,
    "STREETLIGHT_FAILURE": IssueType.BROKEN_STREETLIGHT,
    "STREETLIGHT_DAMAGE": IssueType.BROKEN_STREETLIGHT,
    "SEWER_OVERFLOW": IssueType.SEWAGE_OVERFLOW,
    "WATERLOGGING": IssueType.FLOODING,
    "BLOCKED_DRAIN": IssueType.FLOODING,
    "WATER_LEAKAGE": IssueType.WATER_LEAK,
    "BROKEN_PIPELINE": IssueType.WATER_LEAK,
    "ELECTRICAL_INFRASTRUCTURE": IssueType.OTHER,
    "OVERFLOWING_BIN": IssueType.OTHER,
    "GARBAGE_ACCUMULATION": IssueType.OTHER,
}

# Map asset_id prefix to AssetType
ASSET_ID_PREFIX_MAP: dict[str, AssetType] = {
    "AST-ROAD": AssetType.ROAD,
    "AST-DRN": AssetType.DRAIN,
    "AST-SWR": AssetType.SEWER,
    "AST-WTR": AssetType.WATER_MAIN,
    "AST-STL": AssetType.STREETLIGHT,
    "AST-ELE": AssetType.OTHER,
}

EVIDENCE_TYPE_MAP: dict[str, EvidenceType] = {
    "CITIZEN_PHOTO": EvidenceType.IMAGE,
    "AFTER_PHOTO": EvidenceType.IMAGE,
    "DOCUMENTARY_EVIDENCE": EvidenceType.TEXT,
    "FIELD_INSPECTION": EvidenceType.TEXT,
    "AUTHORITY_UPDATE": EvidenceType.TEXT,
}

VERIFICATION_RESULT_MAP: dict[str, VerificationResult] = {
    "FULLY_RESOLVED": VerificationResult.FULLY_RESOLVED,
    "NOT_RESOLVED": VerificationResult.NOT_RESOLVED,
    "UNRESOLVED": VerificationResult.NOT_RESOLVED,
    "NO_EVIDENCE": VerificationResult.NO_EVIDENCE,
    "INSUFFICIENT_EVIDENCE": VerificationResult.NO_EVIDENCE,
    "HUMAN_REVIEW": VerificationResult.HUMAN_REVIEW,
}

INCIDENT_STATUS_FROM_RESOLUTION: dict[str, IncidentStatus] = {
    "FULLY_RESOLVED": IncidentStatus.RESOLVED,
    "NOT_RESOLVED": IncidentStatus.ACTIVE,
    "UNRESOLVED": IncidentStatus.ACTIVE,
    "NO_EVIDENCE": IncidentStatus.DRAFT,
    "INSUFFICIENT_EVIDENCE": IncidentStatus.DRAFT,
    "HUMAN_REVIEW": IncidentStatus.UNDER_REVIEW,
}


def resolve_asset_type(asset_id: str) -> AssetType:
    for prefix, at in ASSET_ID_PREFIX_MAP.items():
        if asset_id.startswith(prefix):
            return at
    return AssetType.OTHER


def promote_to_multipolygon(geom_dict: dict | None) -> dict | None:
    """Promote a Polygon geometry to MultiPolygon if needed."""
    if geom_dict is None:
        return None
    gtype = geom_dict.get("type")
    if gtype == "MultiPolygon":
        return geom_dict
    if gtype == "Polygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [geom_dict["coordinates"]],
        }
    return None


# ---------------------------------------------------------------------------
# Seed: Authorities
# ---------------------------------------------------------------------------

async def seed_authorities(
    session: AsyncSession, data: dict
) -> dict[str, uuid.UUID]:
    """Seed authorities from lucknow_authority_master.json."""
    c = _counter("authorities")
    auth_id_map: dict[str, uuid.UUID] = {}

    for a in data.get("authorities", []):
        src_id: str = a["authority_id"]
        uid = det_uuid(src_id)
        auth_id_map[src_id] = uid

        existing = await session.get(Authority, uid)
        if existing is not None:
            c["existing"] += 1
            print(f"    [exists] {src_id}")
            continue

        obj = Authority(
            id=uid,
            name=a["authority_name"],
            short_code=src_id,
            description=f"{a['authority_type']} — {a['authority_name']}",
            website_url=a.get("official_portal"),
            is_active=True,
            # Conservative defaults; SLA rules CSV has per-category overrides
            sla_hours_low=168,
            sla_hours_medium=72,
            sla_hours_high=24,
            sla_hours_critical=4,
        )
        session.add(obj)
        c["inserted"] += 1
        print(f"    [insert] {src_id} -> {uid}")

    return auth_id_map


# ---------------------------------------------------------------------------
# Seed: Jurisdictions
# ---------------------------------------------------------------------------

MISSING_GEOMETRY_WARDS = {"WARD-001", "WARD-007", "WARD-009", "WARD-012", "WARD-014"}


async def seed_jurisdictions(
    session: AsyncSession,
    auth_id_map: dict[str, uuid.UUID],
    lmc_id: uuid.UUID,
) -> dict[str, uuid.UUID]:
    """Seed 8 zones and 110 wards as Jurisdiction rows."""
    c = _counter("jurisdictions")
    jur_id_map: dict[str, uuid.UUID] = {}

    # ---- Zones ----
    zones_geojson = json.loads(
        read_source_file("data/gis/verified/lucknow_zones_verified.geojson")
    )
    for feat in zones_geojson["features"]:
        props = feat.get("properties") or {}
        src_id = (
            props.get("zone_id")
            or props.get("ZONE_ID")
            or props.get("Zone_ID")
            or ""
        )
        if not src_id:
            continue

        uid = det_uuid(src_id)
        jur_id_map[src_id] = uid

        existing = await session.get(Jurisdiction, uid)
        if existing is not None:
            c["existing"] += 1
            continue

        geom_raw = promote_to_multipolygon(feat.get("geometry"))
        boundary = None
        if geom_raw:
            try:
                shp = shape(geom_raw)
                boundary = from_shape(shp, srid=4326)
            except Exception as e:
                print(f"    [warn ] {src_id} geometry error: {e}")

        zone_name = (
            props.get("zone_name")
            or props.get("ZONE_NAME")
            or props.get("Zone_Name")
            or src_id
        )
        obj = Jurisdiction(
            id=uid,
            name=zone_name,
            code=src_id,
            description=f"Administrative zone — {zone_name}",
            authority_id=lmc_id,
            boundary=boundary,
        )
        session.add(obj)
        c["inserted"] += 1
        print(f"    [insert] zone {src_id}")

    await session.flush()

    # ---- Wards ----
    wards_geojson = json.loads(
        read_source_file("data/gis/verified/lucknow_wards_verified.geojson")
    )
    for feat in wards_geojson["features"]:
        props = feat.get("properties") or {}
        src_id = (
            props.get("ward_id")
            or props.get("WARD_ID")
            or props.get("Ward_ID")
            or ""
        )
        if not src_id:
            continue

        uid = det_uuid(src_id)
        jur_id_map[src_id] = uid

        existing = await session.get(Jurisdiction, uid)
        if existing is not None:
            c["existing"] += 1
            continue

        boundary = None
        if src_id not in MISSING_GEOMETRY_WARDS:
            geom_raw = promote_to_multipolygon(feat.get("geometry"))
            if geom_raw:
                try:
                    shp = shape(geom_raw)
                    boundary = from_shape(shp, srid=4326)
                except Exception as e:
                    print(f"    [warn ] {src_id} geometry error: {e}")

        ward_name = (
            props.get("ward_name")
            or props.get("WARD_NAME")
            or props.get("Ward_Name")
            or src_id
        )
        obj = Jurisdiction(
            id=uid,
            name=ward_name,
            code=src_id,
            description=f"Municipal ward -- {ward_name}",
            authority_id=lmc_id,
            boundary=boundary,
        )
        session.add(obj)
        c["inserted"] += 1

    # ---- Wards with missing geometry (from jurisdiction_registry.csv) ----
    registry_rows = parse_csv(
        read_source_file("data/gis/verified/jurisdiction_registry.csv")
    )
    for row in registry_rows:
        src_id = row.get("ward_id", "").strip()
        if not src_id or src_id in jur_id_map:
            continue

        uid = det_uuid(src_id)
        jur_id_map[src_id] = uid

        existing = await session.get(Jurisdiction, uid)
        if existing is not None:
            c["existing"] += 1
            continue

        hindi = row.get("ward_name_hindi", "").strip()
        en = row.get("ward_name_en", "").strip()
        ward_name = f"{hindi} ({en})" if hindi and en else (en or hindi or src_id)

        obj = Jurisdiction(
            id=uid,
            name=ward_name,
            code=src_id,
            description=f"Municipal ward -- {ward_name}",
            authority_id=lmc_id,
            boundary=None,  # missing boundary, do not fabricate geometry
        )
        session.add(obj)
        c["inserted"] += 1
        print(f"    [insert] ward (missing boundary) {src_id} -> {uid}")

    print(f"    Wards queued for insertion")
    return jur_id_map


# ---------------------------------------------------------------------------
# Seed: Incidents + Locations
# ---------------------------------------------------------------------------

async def seed_incidents(
    session: AsyncSession,
    auth_id_map: dict[str, uuid.UUID],
    jur_id_map: dict[str, uuid.UUID],
) -> dict[str, uuid.UUID]:
    """Seed 20 incidents with their locations and INCIDENT_CREATED events."""
    c_inc = _counter("incidents")
    c_loc = _counter("locations")
    c_evt = _counter("events")
    inc_id_map: dict[str, uuid.UUID] = {}

    rows = parse_csv(read_source_file("data/lucknow/incidents/seed_incidents.csv"))
    for row in rows:
        src_id = row["incident_id"]
        uid = det_uuid(src_id)
        inc_id_map[src_id] = uid

        existing = await session.get(Incident, uid)
        if existing is not None:
            c_inc["existing"] += 1
            print(f"    [exists] {src_id}")
            continue

        # --- Location ---
        lat = parse_float(row.get("latitude", ""))
        lng = parse_float(row.get("longitude", ""))
        loc_id: uuid.UUID | None = None

        if lat is not None and lng is not None:
            loc_uid = det_uuid(f"loc:{src_id}")
            existing_loc = await session.get(Location, loc_uid)
            if existing_loc is None:
                geom_wkt = f"SRID=4326;POINT({lng} {lat})"
                loc = Location(
                    id=loc_uid,
                    latitude=lat,
                    longitude=lng,
                    geom=WKTElement(geom_wkt, srid=4326),
                    city="Lucknow",
                    state="Uttar Pradesh",
                    country="India",
                )
                session.add(loc)
                c_loc["inserted"] += 1
            else:
                c_loc["existing"] += 1
            loc_id = loc_uid

        # --- Authority + Jurisdiction ---
        auth_src = row.get("authority_id", "")
        authority_id = auth_id_map.get(auth_src)

        ward_src = row.get("ward_id", "")
        zone_src = row.get("zone_id", "")
        jurisdiction_id = jur_id_map.get(ward_src) or jur_id_map.get(zone_src)

        # --- Issue type ---
        issue_cat = row.get("issue_category", "").strip()
        issue_type = ISSUE_TYPE_MAP.get(issue_cat)

        # --- Timestamps ---
        created_at = parse_dt(row.get("created_at", "")) or datetime.now(timezone.utc)

        inc = Incident(
            id=uid,
            reference_number=src_id,
            status=IncidentStatus.ACTIVE,
            issue_type=issue_type,
            title=f"{issue_cat.replace('_', ' ').title()}: {row.get('issue_subcategory', '')}",
            description=row.get("description", ""),
            location_id=loc_id,
            jurisdiction_id=jurisdiction_id,
            authority_id=authority_id,
            evidence_count=0,
        )
        inc.created_at = created_at
        session.add(inc)
        c_inc["inserted"] += 1

        # --- INCIDENT_CREATED timeline event ---
        evt = IncidentEvent(
            id=det_uuid(f"evt:created:{src_id}"),
            incident_id=uid,
            event_type=EventType.INCIDENT_CREATED,
            actor="seed_lucknow_data",
            summary=f"Incident seeded from {row.get('source_id', 'seed')}",
            detail=row.get("notes", ""),
            payload={
                "source_id": row.get("source_id"),
                "source_reference": row.get("source_reference"),
                "record_type": row.get("record_type"),
                "language": row.get("language"),
                "severity": row.get("severity"),
            },
        )
        evt.created_at = created_at
        session.add(evt)
        c_evt["inserted"] += 1

        print(f"    [insert] {src_id} -> {uid}")

    return inc_id_map


# ---------------------------------------------------------------------------
# Seed: Assets
# ---------------------------------------------------------------------------

async def seed_assets(
    session: AsyncSession,
    inc_id_map: dict[str, uuid.UUID],
) -> None:
    """Seed assets referenced by seed incidents (asset_id != UNKNOWN/NEEDS_REVIEW)."""
    c = _counter("assets")

    # Build asset_id -> incident_src_id map from seed_incidents.csv
    incident_rows = parse_csv(read_source_file("data/lucknow/incidents/seed_incidents.csv"))
    asset_to_incident: dict[str, str] = {}
    for row in incident_rows:
        a_id = row.get("asset_id", "").strip()
        if a_id and a_id not in ("UNKNOWN", "NEEDS_REVIEW", ""):
            asset_to_incident[a_id] = row["incident_id"]

    asset_rows = parse_csv(read_source_file("data/lucknow/assets/asset_ownership.csv"))
    for row in asset_rows:
        asset_src_id = row["asset_id"]

        if asset_src_id not in asset_to_incident:
            c["skipped"] += 1
            continue

        inc_src_id = asset_to_incident[asset_src_id]
        inc_uuid = inc_id_map.get(inc_src_id)
        if inc_uuid is None:
            c["skipped"] += 1
            continue

        uid = det_uuid(f"asset:{asset_src_id}")
        existing = await session.get(Asset, uid)
        if existing is not None:
            c["existing"] += 1
            continue

        asset_type = resolve_asset_type(asset_src_id)

        obj = Asset(
            id=uid,
            incident_id=inc_uuid,
            asset_type=asset_type,
            name=row.get("asset_name"),
            external_asset_id=asset_src_id,
            description=row.get("notes"),
            extra_metadata={
                "authority_id": row.get("authority_id"),
                "responsibility_status": row.get("responsibility_status"),
                "location_status": row.get("location_status"),
                "verification_status": row.get("verification_status"),
            },
        )
        session.add(obj)
        c["inserted"] += 1
        print(f"    [insert] {asset_src_id} -> incident {inc_src_id}")


# ---------------------------------------------------------------------------
# Seed: Evidence + VerificationRecords
# ---------------------------------------------------------------------------

async def seed_evidence(
    session: AsyncSession,
    inc_id_map: dict[str, uuid.UUID],
) -> None:
    """Seed 13 evidence rows and create VerificationRecords where applicable."""
    c_ev = _counter("evidence")
    c_vr = _counter("verification_records")
    c_loc = _counter("evidence_locations")

    # Track per-incident verification state
    verification_map: dict[str, dict] = {}

    rows = parse_csv(read_source_file("data/lucknow/evidence/evidence.csv"))
    for row in rows:
        evd_src_id = row["evidence_id"]
        inc_src_id = row.get("incident_id", "")
        inc_uuid = inc_id_map.get(inc_src_id)

        uid = det_uuid(f"evd:{evd_src_id}")
        existing = await session.get(Evidence, uid)
        if existing is not None:
            c_ev["existing"] += 1
            continue

        ev_type_raw = row.get("evidence_type", "")
        ev_type = EVIDENCE_TYPE_MAP.get(ev_type_raw, EvidenceType.TEXT)

        is_verification = (
            row.get("evidence_stage", "") == "AFTER"
            and row.get("evidence_scope", "") == "RESOLUTION"
        )

        # --- Evidence location ---
        lat = parse_float(row.get("latitude", ""))
        lng = parse_float(row.get("longitude", ""))
        loc_id: uuid.UUID | None = None
        if lat is not None and lng is not None:
            loc_uid = det_uuid(f"evdloc:{evd_src_id}")
            existing_loc = await session.get(Location, loc_uid)
            if existing_loc is None:
                geom_wkt = f"SRID=4326;POINT({lng} {lat})"
                loc = Location(
                    id=loc_uid,
                    latitude=lat,
                    longitude=lng,
                    geom=WKTElement(geom_wkt, srid=4326),
                    city="Lucknow",
                    state="Uttar Pradesh",
                    country="India",
                )
                session.add(loc)
                c_loc["inserted"] += 1
            else:
                c_loc["existing"] += 1
            loc_id = loc_uid

        file_path = row.get("file_path", "").strip()
        storage_key = file_path if file_path else None
        capture_time = parse_dt(row.get("capture_time", ""))

        confidence_raw = row.get("confidence", "")
        try:
            ai_conf = float(confidence_raw) if confidence_raw else None
        except ValueError:
            ai_conf = None

        ev = Evidence(
            id=uid,
            evidence_type=ev_type,
            status=EvidenceStatus.PROCESSED,
            incident_id=inc_uuid,
            location_id=loc_id,
            storage_key=storage_key,
            description=row.get("notes", ""),
            occurred_at=capture_time,
            is_verification_evidence=is_verification,
            ai_confidence=ai_conf,
        )
        if capture_time:
            ev.created_at = capture_time
        session.add(ev)
        c_ev["inserted"] += 1

        # Track for VerificationRecord
        resolution_label = row.get("resolution_label", "").strip()
        if resolution_label and inc_src_id:
            if inc_src_id not in verification_map:
                verification_map[inc_src_id] = {
                    "resolution_label": resolution_label,
                    "before_evd_id": None,
                    "after_evd_id": None,
                    "confidence": ai_conf,
                }
            stage = row.get("evidence_stage", "")
            if stage == "BEFORE" and verification_map[inc_src_id]["before_evd_id"] is None:
                verification_map[inc_src_id]["before_evd_id"] = uid
            elif stage == "AFTER":
                verification_map[inc_src_id]["after_evd_id"] = uid
                verification_map[inc_src_id]["resolution_label"] = resolution_label

        print(f"    [insert] {evd_src_id} ({ev_type_raw} -> {ev_type.value})")

    # Flush so evidence FKs are valid for VerificationRecord
    await session.flush()

    # --- VerificationRecords ---
    for inc_src_id, vdata in verification_map.items():
        resolution_label = vdata["resolution_label"]
        result = VERIFICATION_RESULT_MAP.get(resolution_label)
        if result is None:
            continue

        inc_uuid = inc_id_map.get(inc_src_id)
        if inc_uuid is None:
            continue

        vr_uid = det_uuid(f"vr:{inc_src_id}")
        existing_vr = await session.get(VerificationRecord, vr_uid)
        if existing_vr is not None:
            c_vr["existing"] += 1
            continue

        vr = VerificationRecord(
            id=vr_uid,
            incident_id=inc_uuid,
            before_evidence_id=vdata.get("before_evd_id"),
            after_evidence_id=vdata.get("after_evd_id"),
            result=result,
            confidence=vdata.get("confidence"),
            explanation=f"Seeded from Lucknow data: {resolution_label}",
            verified_by="seed_lucknow_data",
            verified_at=datetime.now(timezone.utc),
        )
        session.add(vr)
        c_vr["inserted"] += 1

        # Update incident status based on verification result
        inc_obj = await session.get(Incident, inc_uuid)
        if inc_obj is not None:
            new_status = INCIDENT_STATUS_FROM_RESOLUTION.get(
                resolution_label, IncidentStatus.ACTIVE
            )
            inc_obj.status = new_status

        print(f"    [insert] VerificationRecord {inc_src_id} -> {result.value}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_seeder(dry_run: bool = False) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    print()
    print("=" * 64)
    print("  CivicTrace -- Lucknow Data Seeder")
    print("=" * 64)
    if dry_run:
        print("  *** DRY RUN -- no changes will be committed ***")
    print()

    try:
        async with async_session() as session:
            async with session.begin():
                # 1. Authorities
                print("[1/5] Seeding authorities ...")
                authority_json = json.loads(
                    read_source_file("data/authority/lucknow_authority_master.json")
                )
                auth_id_map = await seed_authorities(session, authority_json)
                lmc_id = auth_id_map.get("AUTH-LMC", det_uuid("AUTH-LMC"))
                print()

                # 2. Jurisdictions
                print("[2/5] Seeding jurisdictions (zones + wards) ...")
                jur_id_map = await seed_jurisdictions(session, auth_id_map, lmc_id)
                print()

                # 3. Incidents + Locations
                print("[3/5] Seeding incidents + locations ...")
                inc_id_map = await seed_incidents(session, auth_id_map, jur_id_map)
                print()

                # 4. Assets
                print("[4/5] Seeding assets ...")
                await seed_assets(session, inc_id_map)
                print()

                # 5. Evidence + Verification
                print("[5/5] Seeding evidence + verification records ...")
                await seed_evidence(session, inc_id_map)
                print()

                if dry_run:
                    print("  *** DRY RUN: rolling back ***")
                    raise Exception("__DRY_RUN__")

                print("  Committing transaction ...")

    except Exception as exc:
        if str(exc) == "__DRY_RUN__":
            print("  Rollback complete (dry run).")
        else:
            print(f"\n  ERROR: {exc}")
            print("  Transaction rolled back. Database unchanged.")
            raise

    finally:
        await engine.dispose()

    # Summary report
    print()
    print("=" * 64)
    print("  SEED REPORT")
    print("=" * 64)
    print(f"  {'Entity':<30} {'Inserted':>8} {'Existing':>8} {'Skipped':>8}")
    print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8}")
    for name, c in COUNTS.items():
        print(
            f"  {name:<30} {c['inserted']:>8} {c['existing']:>8}"
            f" {c.get('skipped', 0):>8}"
        )
    print("=" * 64)
    print()
    if not dry_run:
        print("  Done. Data committed to database.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed CivicTrace with validated Lucknow data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing to DB",
    )
    args = parser.parse_args()
    asyncio.run(run_seeder(dry_run=args.dry_run))


if __name__ == "__main__":
    main()

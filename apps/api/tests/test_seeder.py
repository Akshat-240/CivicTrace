"""
test_seeder.py
==============
Unit tests for the seed_lucknow_data.py transformation logic.

Tests cover:
- Deterministic UUID generation
- Issue category mapping
- Asset type mapping from ID prefix
- MultiPolygon promotion
- Evidence type mapping
- Verification result mapping
- Incident status from resolution label
- Idempotency (existing rows are skipped)
- Unknown enum rejection (unmapped categories produce None/OTHER)
"""

from __future__ import annotations

import uuid
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Bootstrap the scripts/seed_lucknow_data.py module for testing
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent.parent  # project root
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "apps" / "api"))

import seed_lucknow_data as seeder
from app.models.enums import (
    IssueType,
    AssetType,
    EvidenceType,
    VerificationResult,
    IncidentStatus,
)


# ===========================================================================
# 1. Deterministic UUID generation
# ===========================================================================

class TestDetUUID:
    def test_same_input_same_output(self):
        a = seeder.det_uuid("AUTH-LMC")
        b = seeder.det_uuid("AUTH-LMC")
        assert a == b

    def test_different_inputs_different_outputs(self):
        a = seeder.det_uuid("AUTH-LMC")
        b = seeder.det_uuid("AUTH-UPPWD")
        assert a != b

    def test_is_uuid5(self):
        u = seeder.det_uuid("AUTH-LMC")
        assert isinstance(u, uuid.UUID)
        assert u.version == 5

    def test_auth_lmc_deterministic_value(self):
        # Pinning the exact value prevents silent drift
        expected = uuid.uuid5(uuid.NAMESPACE_DNS, "AUTH-LMC")
        assert seeder.det_uuid("AUTH-LMC") == expected

    def test_ward_prefix_distinct_from_zone_prefix(self):
        ward = seeder.det_uuid("WARD-034")
        zone = seeder.det_uuid("ZONE-01")
        assert ward != zone

    def test_evidence_prefix_namespace(self):
        e1 = seeder.det_uuid("evd:CT-EVD-001")
        e2 = seeder.det_uuid("CT-EVD-001")
        assert e1 != e2  # namespace prefix isolates evidence UUIDs


# ===========================================================================
# 2. Issue category mapping
# ===========================================================================

class TestIssueCategoryMapping:
    @pytest.mark.parametrize("cat, expected", [
        ("POTHOLE", IssueType.POTHOLE),
        ("ROAD_DAMAGE", IssueType.ROAD_DAMAGE),
        ("ILLEGAL_DUMPING", IssueType.ILLEGAL_DUMPING),
        ("STREETLIGHT_FAILURE", IssueType.BROKEN_STREETLIGHT),
        ("STREETLIGHT_DAMAGE", IssueType.BROKEN_STREETLIGHT),
        ("SEWER_OVERFLOW", IssueType.SEWAGE_OVERFLOW),
        ("WATERLOGGING", IssueType.FLOODING),
        ("BLOCKED_DRAIN", IssueType.FLOODING),
        ("WATER_LEAKAGE", IssueType.WATER_LEAK),
        ("BROKEN_PIPELINE", IssueType.WATER_LEAK),
        ("ELECTRICAL_INFRASTRUCTURE", IssueType.OTHER),
        ("OVERFLOWING_BIN", IssueType.OTHER),
        ("GARBAGE_ACCUMULATION", IssueType.OTHER),
    ])
    def test_known_mappings(self, cat, expected):
        assert seeder.ISSUE_TYPE_MAP.get(cat) == expected

    def test_unknown_category_returns_none(self):
        # Unknown categories must not raise; they return None
        result = seeder.ISSUE_TYPE_MAP.get("TOTALLY_UNKNOWN_CATEGORY")
        assert result is None

    def test_map_is_exhaustive_for_seed_data(self):
        """Every category used in seed_incidents.csv must be mapped."""
        seed_categories = {
            "POTHOLE", "ROAD_DAMAGE", "ILLEGAL_DUMPING",
            "STREETLIGHT_FAILURE", "SEWER_OVERFLOW", "WATERLOGGING",
            "BLOCKED_DRAIN", "WATER_LEAKAGE", "BROKEN_PIPELINE",
            "ELECTRICAL_INFRASTRUCTURE",
        }
        for cat in seed_categories:
            assert cat in seeder.ISSUE_TYPE_MAP, f"{cat} missing from ISSUE_TYPE_MAP"


# ===========================================================================
# 3. Asset type mapping from ID prefix
# ===========================================================================

class TestAssetTypeMapping:
    @pytest.mark.parametrize("asset_id, expected", [
        ("AST-ROAD-001", AssetType.ROAD),
        ("AST-ROAD-006", AssetType.ROAD),
        ("AST-DRN-001", AssetType.DRAIN),
        ("AST-DRN-002", AssetType.DRAIN),
        ("AST-SWR-001", AssetType.SEWER),
        ("AST-SWR-004", AssetType.SEWER),
        ("AST-WTR-001", AssetType.WATER_MAIN),
        ("AST-WTR-002", AssetType.WATER_MAIN),
        ("AST-STL-004", AssetType.STREETLIGHT),
        ("AST-STL-005", AssetType.STREETLIGHT),
        ("AST-ELE-003", AssetType.OTHER),
        ("AST-ELE-005", AssetType.OTHER),
    ])
    def test_asset_prefix_resolution(self, asset_id, expected):
        assert seeder.resolve_asset_type(asset_id) == expected

    def test_unknown_prefix_returns_other(self):
        assert seeder.resolve_asset_type("AST-UNKNOWN-999") == AssetType.OTHER

    def test_empty_id_returns_other(self):
        assert seeder.resolve_asset_type("") == AssetType.OTHER


# ===========================================================================
# 4. MultiPolygon promotion
# ===========================================================================

class TestMultiPolygonPromotion:
    def _polygon(self):
        return {
            "type": "Polygon",
            "coordinates": [[[80.0, 26.0], [81.0, 26.0], [81.0, 27.0], [80.0, 27.0], [80.0, 26.0]]],
        }

    def _multipolygon(self):
        return {
            "type": "MultiPolygon",
            "coordinates": [[[[80.0, 26.0], [81.0, 26.0], [81.0, 27.0], [80.0, 26.0]]]],
        }

    def test_polygon_promoted_to_multipolygon(self):
        result = seeder.promote_to_multipolygon(self._polygon())
        assert result is not None
        assert result["type"] == "MultiPolygon"
        assert result["coordinates"] == [self._polygon()["coordinates"]]

    def test_multipolygon_returned_unchanged(self):
        mp = self._multipolygon()
        result = seeder.promote_to_multipolygon(mp)
        assert result == mp

    def test_none_input_returns_none(self):
        assert seeder.promote_to_multipolygon(None) is None

    def test_unknown_type_returns_none(self):
        assert seeder.promote_to_multipolygon({"type": "Point", "coordinates": [80, 26]}) is None

    def test_promoted_coordinates_are_wrapped(self):
        poly = self._polygon()
        result = seeder.promote_to_multipolygon(poly)
        # MultiPolygon coords must be list-of-list-of-rings
        assert isinstance(result["coordinates"][0], list)


# ===========================================================================
# 5. Evidence type mapping
# ===========================================================================

class TestEvidenceTypeMapping:
    @pytest.mark.parametrize("raw, expected", [
        ("CITIZEN_PHOTO", EvidenceType.IMAGE),
        ("AFTER_PHOTO", EvidenceType.IMAGE),
        ("DOCUMENTARY_EVIDENCE", EvidenceType.TEXT),
        ("FIELD_INSPECTION", EvidenceType.TEXT),
        ("AUTHORITY_UPDATE", EvidenceType.TEXT),
    ])
    def test_known_evidence_types(self, raw, expected):
        assert seeder.EVIDENCE_TYPE_MAP.get(raw) == expected

    def test_unknown_type_falls_back_to_text(self):
        # Caller uses .get(raw, EvidenceType.TEXT) — test that pattern works
        result = seeder.EVIDENCE_TYPE_MAP.get("VIDEO_CLIP", EvidenceType.TEXT)
        assert result == EvidenceType.TEXT


# ===========================================================================
# 6. Verification result mapping
# ===========================================================================

class TestVerificationResultMapping:
    @pytest.mark.parametrize("label, expected", [
        ("FULLY_RESOLVED", VerificationResult.FULLY_RESOLVED),
        ("PARTIALLY_RESOLVED", VerificationResult.PARTIALLY_RESOLVED),
        ("UNRESOLVED", VerificationResult.UNRESOLVED),
        ("NOT_RESOLVED", VerificationResult.UNRESOLVED),
        ("INSUFFICIENT_EVIDENCE", VerificationResult.INSUFFICIENT_EVIDENCE),
    ])
    def test_resolution_labels(self, label, expected):
        assert seeder.VERIFICATION_RESULT_MAP.get(label) == expected

    def test_unknown_label_returns_none(self):
        assert seeder.VERIFICATION_RESULT_MAP.get("MADE_UP_STATUS") is None


# ===========================================================================
# 7. Incident status from resolution label
# ===========================================================================

class TestIncidentStatusFromResolution:
    @pytest.mark.parametrize("label, expected_status", [
        ("FULLY_RESOLVED", IncidentStatus.RESOLVED),
        ("PARTIALLY_RESOLVED", IncidentStatus.UNDER_REVIEW),
        ("UNRESOLVED", IncidentStatus.ACTIVE),
        ("NOT_RESOLVED", IncidentStatus.ACTIVE),
        ("INSUFFICIENT_EVIDENCE", IncidentStatus.DRAFT),
    ])
    def test_status_mapping(self, label, expected_status):
        assert seeder.INCIDENT_STATUS_FROM_RESOLUTION.get(label) == expected_status

    def test_unknown_resolution_returns_none(self):
        assert seeder.INCIDENT_STATUS_FROM_RESOLUTION.get("???") is None


# ===========================================================================
# 8. parse_float — zero treated as missing
# ===========================================================================

class TestParseFloat:
    def test_valid_float(self):
        assert seeder.parse_float("26.85028") == pytest.approx(26.85028)

    def test_zero_returns_none(self):
        # 0.0 coordinates are invalid locations — must be treated as missing
        assert seeder.parse_float("0.0") is None
        assert seeder.parse_float("0") is None

    def test_empty_string_returns_none(self):
        assert seeder.parse_float("") is None

    def test_non_numeric_returns_none(self):
        assert seeder.parse_float("N/A") is None

    def test_negative_float(self):
        assert seeder.parse_float("-26.5") == pytest.approx(-26.5)


# ===========================================================================
# 9. parse_dt — datetime parsing
# ===========================================================================

class TestParseDt:
    def test_iso_utc_z(self):
        dt = seeder.parse_dt("2026-08-15T11:20:00Z")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 8
        assert dt.day == 15

    def test_empty_returns_none(self):
        assert seeder.parse_dt("") is None
        assert seeder.parse_dt("   ") is None

    def test_invalid_returns_none(self):
        assert seeder.parse_dt("not-a-date") is None


# ===========================================================================
# 10. Missing geometry wards constant
# ===========================================================================

class TestMissingGeometryWards:
    def test_known_missing_wards_in_set(self):
        for w in ["WARD-001", "WARD-007", "WARD-009", "WARD-012", "WARD-014"]:
            assert w in seeder.MISSING_GEOMETRY_WARDS

    def test_non_missing_ward_not_in_set(self):
        assert "WARD-034" not in seeder.MISSING_GEOMETRY_WARDS
        assert "WARD-109" not in seeder.MISSING_GEOMETRY_WARDS


# ===========================================================================
# 11. Jurisdiction source reconciliation
# ===========================================================================

class TestJurisdictionSourceReconciliation:
    def test_registry_contains_110_wards(self):
        content = seeder.read_source_file("data/gis/verified/jurisdiction_registry.csv")
        rows = seeder.parse_csv(content)
        assert len(rows) == 110

    def test_geojson_contains_105_wards(self):
        content = seeder.read_source_file("data/gis/verified/lucknow_wards_verified.geojson")
        data = json.loads(content)
        assert len(data["features"]) == 105

    def test_zones_geojson_contains_8_zones(self):
        content = seeder.read_source_file("data/gis/verified/lucknow_zones_verified.geojson")
        data = json.loads(content)
        assert len(data["features"]) == 8

    def test_missing_geometry_wards_are_exact_difference(self):
        reg_content = seeder.read_source_file("data/gis/verified/jurisdiction_registry.csv")
        reg_rows = seeder.parse_csv(reg_content)
        reg_ids = {r["ward_id"] for r in reg_rows}

        gj_content = seeder.read_source_file("data/gis/verified/lucknow_wards_verified.geojson")
        gj_data = json.loads(gj_content)
        gj_ids = {
            f["properties"].get("ward_id") or f["properties"].get("WARD_ID")
            for f in gj_data["features"]
        }

        diff = reg_ids - gj_ids
        assert diff == seeder.MISSING_GEOMETRY_WARDS
        assert len(diff) == 5


# ===========================================================================
# 12. Asset source reconciliation
# ===========================================================================

class TestAssetSourceReconciliation:
    def test_asset_ownership_contains_39_records(self):
        content = seeder.read_source_file("data/lucknow/assets/asset_ownership.csv")
        rows = seeder.parse_csv(content)
        assert len(rows) == 39

    def test_incidents_reference_16_valid_assets(self):
        content = seeder.read_source_file("data/lucknow/incidents/seed_incidents.csv")
        rows = seeder.parse_csv(content)
        assert len(rows) == 20
        valid_assets = [
            r["asset_id"].strip()
            for r in rows
            if r.get("asset_id", "").strip() not in ("UNKNOWN", "NEEDS_REVIEW", "")
        ]
        assert len(valid_assets) == 16
        # All 16 referenced asset IDs are unique
        assert len(set(valid_assets)) == 16

    def test_asset_mathematical_reconciliation(self):
        asset_content = seeder.read_source_file("data/lucknow/assets/asset_ownership.csv")
        asset_rows = seeder.parse_csv(asset_content)
        total_assets = len(asset_rows)

        inc_content = seeder.read_source_file("data/lucknow/incidents/seed_incidents.csv")
        inc_rows = seeder.parse_csv(inc_content)
        referenced_ids = {
            r["asset_id"].strip()
            for r in inc_rows
            if r.get("asset_id", "").strip() not in ("UNKNOWN", "NEEDS_REVIEW", "")
        }

        source_asset_ids = {r["asset_id"] for r in asset_rows}
        referenced_count = len(referenced_ids.intersection(source_asset_ids))
        unreferenced_count = total_assets - referenced_count

        assert total_assets == 39
        assert referenced_count == 16
        assert unreferenced_count == 23
        assert referenced_count + unreferenced_count == total_assets

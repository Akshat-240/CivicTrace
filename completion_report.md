# Gate 4 Hardening Report

## 1. Architecture Adherence
**Confirmed:** No new architecture was added. The CivicTrace Bible remains the governing architecture. The Gate 3 GIS → Authority → Priority → SLA flow was preserved without regression.

## 2. Invariant Confirmation
**Confirmed:** The invariant "IF jurisdiction_id IS NULL THEN authority_id MUST NOT be populated" holds logically in the backend workflow. The `assign_jurisdiction` service only sets `authority_id` when a `JURISDICTION_FOUND` match occurs via PostGIS `ST_Contains`.

## 3. Root Cause of Jurisdiction -> Authority Issue
The root cause was traced to a missing integrity constraint at the database layer. While the core API orchestrator correctly mapped GIS matches, legacy initialization scripts (e.g., `seed_lucknow_data.py`) bypassed the workflow and explicitly injected `authority_id` direct from flat CSV records while `jurisdiction_id` was left empty (NULL). Because the schema had no structural rule linking them, these orphaned assignments persisted and were served to the frontend.

## 4. Exact Fix Made
I introduced a strict PostgreSQL `CheckConstraint` (`ck_incidents_jurisdiction_authority_invariant`) to the `Incident` ORM model, asserting `((jurisdiction_id IS NULL AND authority_id IS NULL) OR (jurisdiction_id IS NOT NULL))`. This physically guarantees at the storage layer that an authority can never exist without a mapped jurisdiction.

## 5. Test File Location
The validation suite encompassing Tests A, B, C, D, and E has been implemented at:
`apps/api/tests/test_gate4_hardening.py`

## 6. UI Input Protection
**Confirmed:** The UI (and API Schemas) strictly prevent users from providing an `authority_id` during incident creation. The `IncidentSubmit` payload solely accepts generic details (like `issue_type` and `location`).

## 7. Idempotency Proof
Test C verifies that running the GIS resolution multiple times on the same coordinate evaluates safely, returning the same matched jurisdiction and authority deterministically without crashing or side-effects.

## 8. Dashboard Scoping Status
The `DashboardPage.jsx` and `IncidentsPage.jsx` rely on a hardcoded context scoping variable (`MOCK_AUTHORITY_ID`) targeting the LMC record. A prominent UI banner has been implemented displaying:
> "DEMO AUTHORITY CONTEXT — NOT AUTHENTICATION (Filtering by hardcoded Lucknow Municipal Corporation ID for Gate 4)"

## 9. Scope Containment
**Confirmed:** Phase 5 features (Evidence upload, AI verification, Duplicate Fusion, real Authentication, Docker) were strictly avoided.

## 10. Orchestration Transaction Integrity
**Confirmed:** The `flush()` patterns and shared `AsyncSession` dependency injection were preserved across the workflow orchestrator.

## 11. Test Results
Execution of `pytest -v apps/api/tests/test_gate4_hardening.py` yielded perfect execution:
- `test_a_positive_gis_path` PASSED
- `test_b_negative_gis_path` PASSED
- `test_c_idempotency` PASSED
- `test_d_orm_api_serialization` PASSED
- `test_e_citizen_regression` PASSED
Overall Result: 5 passed in 1.63s

## 12. Final Declaration
**Gate 4 is HARDENED.**

## 13. Next Steps
Please verify the implementations and run the test suite to confirm the Authority workflow is fully stable before we proceed to Gate 5.

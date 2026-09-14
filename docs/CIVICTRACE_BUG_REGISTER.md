# CivicTrace — Bug & Risk Register, Dead Code, and Integration Gaps

This document catalogues all concrete bugs, architectural risks, dead/unused code, and integration gaps identified across the CivicTrace repository.

---

## 1. Concrete Bug & Risk Register

| ID | Severity | File | Problem Description | Why It Matters | Reproduction Scenario | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | **HIGH** | `app/api/routes/gis.py`<br>`app/main.py` | `app/api/routes/gis.py` defines `GET /gis/jurisdiction`, but `gis.router` is never mounted in `create_app()` in `app/main.py`. | Any external client, test, or frontend component attempting to query `/api/v1/gis/jurisdiction` receives an immediate HTTP 404 Not Found error. | Issue `GET http://localhost:8000/api/v1/gis/jurisdiction?latitude=26.8&longitude=80.9`. Expected 200 with `JurisdictionResult`; actual is 404. | In `app/main.py`, import `gis` from `app.api.routes` and add `app.include_router(gis.router, prefix=settings.api_v1_prefix)`. |
| **BUG-02** | **HIGH** | `app/services/verification_service.py`<br>`app/services/ai/service.py`<br>`app/services/fusion_service.py` | Services execute `await self.session.commit()` directly inside business logic methods instead of relying on transactional scope delegation. | Bypasses the unit-of-work pattern established by `get_db()` in `database.py`. Prevents atomic multi-service orchestration (e.g. if an error occurs after AI processing, partial commits cannot be rolled back). | Call `AIService.process_evidence()` followed by a failing method in the same transaction. The status update to `PROCESSING` or `PROCESSED` is already committed and cannot rollback. | Replace all service-level `await self.session.commit()` calls with `await self.session.flush()`, allowing the route handler / `get_db()` context manager to manage transaction commits. |
| **BUG-03** | **MEDIUM** | `app/services/fusion_service.py`<br>`app/services/incident_service.py` | `FusionService` is fully implemented and tested, but is never invoked during incident creation in `IncidentService.create_incident()`. | Potholes or duplicate reports filed at identical GPS coordinates within minutes of each other are unconditionally created as new incidents rather than being fused. | Submit two identical incidents at `lat: 26.8467, lng: 80.9462` within 5 minutes. Two separate `INC-` records are created; neither is fused. | In `IncidentService.create_incident()` or `EvidenceService.add_evidence()`, check `FusionService.fuse_evidence()` before instantiating a new `Incident`. |
| **BUG-04** | **MEDIUM** | `apps/web/src/pages/citizen/CitizenReportPage.jsx` | `CitizenReportPage.jsx` hardcodes Lucknow coordinates (`latitude: 26.8467, longitude: 80.9462`) for every report submitted. | Citizens submitting reports in other wards or outside the city center will always be mapped to Hazratganj / MG Road. | Submit a report while selecting any location on the map wizard. Check DB `locations` table: latitude and longitude are always `26.8467` and `80.9462`. | Bind the submission payload to the dynamic coordinates selected on the interactive map or device GPS geolocation. |
| **BUG-05** | **MEDIUM** | `app/services/sla_poller.py` | If an exception occurs on an individual incident in `SLAPoller.evaluate_all_active_slas()`, it executes `await self.session.rollback()` on the shared session. | In SQLAlchemy async sessions, rolling back a session invalidates pending queries and can cause subsequent incidents in the same loop to fail with `PendingRollbackError`. | Trigger an error on the first of 5 active incidents during polling. Observe whether subsequent incidents fail due to transaction state. | Create a fresh nested transaction or scoped session per incident during the polling loop. |
| **BUG-06** | **LOW** | `apps/web/src/pages/authority/DashboardPage.jsx`<br>`apps/web/src/pages/authority/IncidentsPage.jsx` | `DashboardPage.jsx` and `IncidentsPage.jsx` hardcode `MOCK_AUTHORITY_ID = "61c6d93e-889d-42fc-b6b9-b167ce631d47"`. | Any incident assigned to an authority other than Lucknow Municipal Corporation is invisible on the authority dashboard. | Create an incident belonging to a different authority. It appears in DB and Admin lists, but disappears from Authority Dashboard. | Implement genuine authentication/session context, or provide an authority selector dropdown for demonstration purposes. |
| **BUG-07** | **LOW** | `apps/web/src/pages/citizen/CitizenFeedbackPage.jsx` | Citizen feedback submission is purely simulated via local React state (`setSubmitted(true)`). No API call or backend storage exists. | Citizen post-resolution ratings and comments are immediately lost on page reload. | Fill out feedback on `/citizen/feedback`, click Submit, then refresh browser. Form resets; no data was persisted. | Create a `Feedback` ORM model, Alembic migration, and `POST /api/v1/incidents/{id}/feedback` route. |

---

## 2. Dead Code, Unused Features, and Duplicated Logic

### A. Dead Code
1. **`app/api/routes/evidence.py`**:
   - Contains an empty `router = APIRouter(prefix="/evidence")` with a comment `# Routes will be added in the next implementation phase.`
   - Evidence endpoints were implemented under `/incidents/{id}/evidence` in `incidents.py`. This file is completely unused.
2. **`app/api/routes/accountability.py`**:
   - Contains an empty `router = APIRouter(prefix="/accountability")`. SLA routes were implemented directly in `incidents.py`.
3. **`app/api/routes/verification.py`**:
   - Contains an empty `router = APIRouter(prefix="/verification")`. Verification routes were implemented directly in `incidents.py`.
4. **`app/core/security.py`**:
   - Implements `create_access_token`, `decode_access_token`, `hash_password`, and `verify_password`.
   - None of the route handlers in `app/api/routes/` currently require authentication or verify JWT tokens. This module is entirely dead at runtime.
5. **Root-Level and App-Level Scratch Scripts**:
   - `apps/api/test_workflow.py`, `test_create.py`, `test_list.py`, `check_db.py`, `verify_issue.py`, `find_bad.py`, `add_constraint.py`, `fix.py`, `write_tests.py`, `test_workflow_query.py`
   - Root-level `test_db.py`, `test_point.py`, `test_workflow_match.py`, `incident_test.json`, `incident_test2.json`
   - These are development scratchpads that should be cleaned or moved to an internal `tools/` folder.

### B. Unused Backend Features (Implemented but Unwired)
1. **`FusionService` (`app/services/fusion_service.py`)**:
   - Complete, tested PostGIS deduplication engine with mathematical scoring and ambiguity handling.
   - Has zero callers in `apps/api/app/` production code (only called in tests).
2. **`POST /api/v1/system/evaluate-slas` (`app/api/routes/system.py`)**:
   - Endpoint exists to manually trigger global SLA evaluation, but no frontend admin UI or external cron invokes it (the background poller loop in `main.py` is used instead).
3. **`POST /api/v1/incidents/{id}/evidence/{evidence_id}/analyze` (`app/api/routes/incidents.py`)**:
   - Endpoint to trigger AI perception on an evidence item. Uncalled by the web application.

### C. Duplicated Logic
1. **Severity Mapping Dictionaries**:
   - `PriorityConfig.SEVERITY_VALUES` in `priority_service.py` maps `CRITICAL: 1.0, HIGH: 0.75, MEDIUM: 0.5, LOW: 0.25`.
   - `VerificationConfig.SEVERITY_VALUES` in `verification_service.py` maps `CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1`.
   - Both represent the ordinal scale of physical severity, but use differing numerical systems. A single shared domain mapper should be used.
2. **Incident Normalization in Frontend**:
   - Both `apps/web/src/pages/authority/DashboardPage.jsx` and `apps/web/src/pages/authority/IncidentsPage.jsx` implement their own slightly different version of `normalizeIncidentListItem()` to format backend responses into table rows.

---

## 3. Integration Gap Register

| Functional Domain | Backend Service | REST API | Database Model | Frontend UI | Automated E2E | Current Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Citizen Incident Reporting** | `IncidentService` | `POST /incidents` | `incidents`, `locations` | `CitizenReportPage` | `test_api_incidents.py`<br>`test_phase5_e2e.py` | **COMPLETE** |
| **GIS Jurisdiction Routing** | `GISService` | Internal / Orchestrated | `jurisdictions`, `locations` | Displayed on Dashboards | `test_gis.py` | **COMPLETE** |
| **Priority Engine Scoring** | `PriorityService` | Internal / Orchestrated | `priorities` | Badges on Dashboards | `test_priority.py` | **COMPLETE** |
| **SLA Clock & Progression** | `AccountabilityService` | Internal / Orchestrated | `slas` | SLA Timers & Status | `test_sla.py`<br>`test_sla_poller.py` | **COMPLETE** |
| **Background SLA Poller** | `SLAPoller` | `POST /system/evaluate-slas` | `slas` | Live SLA indicators | `test_sla_poller.py` | **COMPLETE** |
| **Resolution Submission** | `VerificationService` | `POST /submit-resolution` | `evidence` (`is_verification`) | `VerificationPage` | `test_phase5_e2e.py` | **COMPLETE** |
| **Automated Verification Eval** | `VerificationService` | `POST /verify-resolution` | `verification_records` | `VerificationPage` | `test_verification.py`<br>`test_phase5_e2e.py` | **COMPLETE** |
| **Human Verification Decision** | `VerificationService` | `POST /human-verify` | `verification_records` | `VerificationPage` | `test_phase5_e2e.py` | **COMPLETE** |
| **Explicit Incident Closure** | `IncidentService` | `POST /close` | `incidents.status` | `VerificationPage` | `test_phase5_e2e.py` | **COMPLETE** |
| **Citizen Proof of Resolution** | `IncidentService` | `GET /incidents/{id}` | `verification_records`, `events` | `CitizenTrackPage` | Manual Verification | **COMPLETE** |
| **Incident Fusion / Deduplication** | `FusionService` | None | None | None | `test_fusion.py` | **BACKEND ONLY** (Unwired in API) |
| **AI Perception (Gemini)** | `AIService` | `POST /analyze` | `evidence.ai_*` | None | `test_ai.py` | **BACKEND ONLY** |
| **Binary Object Storage** | None | None | `storage_key` column | Text only | None | **MISSING** (Metadata/Text only) |
| **Citizen Post-Resolution Feedback** | None | None | None | `CitizenFeedbackPage` | None | **FRONTEND ONLY** (Mock State) |
| **Municipal Admin Portal** | None | None | None | 9 Admin Pages | None | **FRONTEND ONLY** (100% Mock Data) |
| **Authentication & RBAC** | `app/core/security.py` | None | None | Simulated in `LoginPage` | None | **SCAFFOLDING** (Hardcoded Demo Context) |
| **Officer / Field Team Assignment** | None | None | None | `AssignmentPage` (Notice) | None | **EXPLICITLY OUT OF SCOPE** |

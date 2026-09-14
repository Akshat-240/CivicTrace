# CivicTrace — Complete Data Flow & Execution Tracing

This document traces the real execution paths of CivicTrace across the 8 primary workflows of the platform, following data from React UI events through network requests, FastAPI controllers, Pydantic validation, domain service logic, PostGIS database queries, and back to state updates.

---

## Architecture Overview Flow Diagram

```
[ Citizen / Public ]             [ Authority Staff ]              [ Municipal Reviewer ]
        │                                 │                                  │
        ▼                                 ▼                                  ▼
[ CitizenReportPage ]             [ IncidentsPage ]                  [ VerificationPage ]
[ CitizenTrackPage  ]             [ DashboardPage ]                          │
        │                                 │                                  │
        └─────────────────────────┬───────┴──────────────────────────────────┘
                                  ▼
                     [ apps/web/src/services/api.js ]
                                  │  (JSON over HTTP)
                                  ▼
                    [ FastAPI Gateway / Routers ]
                      app/api/routes/incidents.py
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
[ Ingestion & Workflows ]   [ Domain Engines ]      [ Verification Engine ]
  IncidentService             GISService              VerificationService
  EvidenceService             PriorityService           (Stage 1: Submit)
                              AccountabilityService     (Stage 2: Auto-Eval)
                              SLAPoller                 (Stage 3: Human Verify)
                                                        IncidentService
                                                        (Stage 4: Close)
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  ▼
                     [ Repositories Layer ]
                      IncidentRepository
                      EvidenceRepository
                      EventRepository
                                  │  (SQLAlchemy Async)
                                  ▼
                [ PostgreSQL 16 + PostGIS Extension ]
                     incidents, locations, slas,
                  jurisdictions, authorities, events,
                   priorities, verification_records
```

---

## FLOW 1: Citizen Creates Incident

This workflow traces how a citizen report is filed, validated, persisted, and immediately orchestrated into the civic intelligence pipeline.

### Step-by-Step Execution Path:
1. **User Interaction (`CitizenReportPage.jsx`)**:
   - The citizen interacts with the 4-step wizard: selects an issue category (e.g., "Road"), enters description text, reviews coordinates, and clicks "Submit Report".
   - An event handler `handleNextStep()` constructs the submission payload:
     ```javascript
     const payload = {
       title: "Road Issue",
       description: "Large pothole on road causing dangerous vehicle congestion.",
       issue_type: "road_damage",
       location: {
         latitude: 26.8467,
         longitude: 80.9462,
         address_raw: "MG Road, Near Hazratganj Crossing"
       }
     };
     ```
2. **API Client (`apps/web/src/services/api.js`)**:
   - `createIncident(payload)` calls `fetchAPI('/incidents', { method: 'POST', body: JSON.stringify(payload) })`.
3. **HTTP Transport**:
   - Client issues `POST http://localhost:8000/api/v1/incidents` with `Content-Type: application/json`.
4. **FastAPI Route Controller (`app/api/routes/incidents.py`)**:
   - Route `create_incident(data: IncidentSubmit, db: DbSession)` intercepts the request.
   - Pydantic validates `data` against `IncidentSubmit` schema.
   - Instantiates `service = IncidentService(db)`.
5. **Database Entities Creation (`app/services/incident_service.py`)**:
   - If `data.location` is provided, creates a `Location` row with `latitude`, `longitude`, `accuracy_meters`, and `address_raw`. Flushes to DB to obtain `location.id`.
   - Generates a reference number (e.g. `INC-F4A1B2C3`).
   - Inserts `Incident` with initial status `IncidentStatus.DRAFT`, `evidence_count=0`.
   - Inserts an `IncidentEvent` record with `event_type=EventType.INCIDENT_CREATED`, `actor="user"`.
   - Flushes transaction.
6. **Synchronous Pipeline Orchestration (`incident_service.py::process_incident_workflow`)**:
   - Automatically executes:
     1. **GIS Routing**: Calls `self.assign_jurisdiction(incident.id)` (see Flow 2).
     2. **Priority Scoring**: Calls `PriorityService(self.session).compute_priority(incident.id)` (see Flow 3).
     3. **SLA Start**: If `incident.authority_id` was resolved by GIS, calls `AccountabilityService(self.session).start_sla(incident.id)` (see Flow 4).
7. **Transaction Commit**:
   - `get_db` FastAPI dependency commits the transaction on route completion.
8. **Response Return**:
   - Returns HTTP 201 with full `IncidentDetail` schema containing embedded `location`, `jurisdiction`, `authority`, `priority`, and `sla`.
9. **Frontend State Transition**:
   - `CitizenReportPage.jsx` sets `submittedId = response.reference_number` and transitions the UI to the success screen with a direct link to track the issue.

---

## FLOW 2: GIS Jurisdiction & Authority Routing

Determines geographic responsibility purely by administrative boundary containment.

### Step-by-Step Execution Path:
1. **Trigger**:
   - Called during incident creation via `IncidentService.process_incident_workflow()` or manually via `POST /api/v1/incidents/{id}/assign-jurisdiction`.
2. **Coordinate Extraction**:
   - `IncidentService.assign_jurisdiction()` retrieves the incident's `Location` coordinates (`latitude`, `longitude`).
   - If coordinates are missing, appends a `SYSTEM_NOTE` event explaining GIS resolution failure.
3. **Spatial Query Execution (`app/services/gis_service.py`)**:
   - `GISService.resolve_jurisdiction(latitude, longitude)` validates coordinate bounds (`-90 <= lat <= 90`, `-180 <= lng <= 180`).
   - Builds a PostGIS spatial point using GeoAlchemy2:
     ```python
     point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
     ```
     *(Note coordinate order: longitude is X, latitude is Y).*
   - Executes SQL against `jurisdictions`:
     ```sql
     SELECT jurisdictions.* 
     FROM jurisdictions 
     WHERE ST_Contains(jurisdictions.boundary, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326));
     ```
4. **Result Resolution & Guardrails**:
   - **Case 0 matches**: Returns `GISStatus.NO_JURISDICTION` ("Coordinates do not fall within any known civic boundary").
   - **Case >1 matches**: Returns `GISStatus.JURISDICTION_CONFLICT` (Multiple overlapping boundaries; flags for human review).
   - **Case 1 match, but no authority linked**: Returns `GISStatus.JURISDICTION_CONFLICT`.
   - **Case 1 clean match**: Returns `GISStatus.JURISDICTION_FOUND`, `jurisdiction_id`, `authority_id`.
5. **Database Update & Audit Events**:
   - Updates `incident.jurisdiction_id` and `incident.authority_id`.
   - Creates `IncidentEvent(event_type=EventType.JURISDICTION_ASSIGNED, summary=...)`.
   - Creates `IncidentEvent(event_type=EventType.AUTHORITY_ASSIGNED, summary=...)`.
   - Flushes session.

---

## FLOW 3: Priority Engine Scoring

Computes a deterministic, explainable priority tier from physical damage, human safety, and persistence.

### Step-by-Step Execution Path:
1. **Trigger**:
   - Executed by `IncidentService.process_incident_workflow()` or `POST /api/v1/incidents/{id}/prioritize`.
2. **Evidence Aggregation (`app/services/priority_service.py`)**:
   - Loads all linked `Evidence` rows for the incident.
   - **Severity Factor**: Extracts the highest severity across all evidence items:
     - `CRITICAL` = 1.0, `HIGH` = 0.75, `MEDIUM` = 0.5, `LOW` = 0.25, `NONE` = 0.0.
   - **Safety Risk Factor**: Checks if ANY evidence has `ai_safety_risk = True` (1.0 if true, 0.0 if false).
   - **Persistence Factor**: Computes ongoing impact based on evidence count and days active:
     ```python
     persistence_score = min(1.0, (evidence_count * 0.1) + (days_active / 30.0))
     ```
3. **Mathematical Weighted Summation**:
   ```python
   total_score = (highest_sev * 0.5) + (safety_score * 0.3) + (persistence_score * 0.2)
   ```
4. **Discrete Threshold Mapping**:
   - `total_score >= 0.75` → `PriorityLevel.CRITICAL`
   - `total_score >= 0.50` → `PriorityLevel.HIGH`
   - `total_score >= 0.25` → `PriorityLevel.MEDIUM`
   - `total_score < 0.25`  → `PriorityLevel.LOW`
5. **Audit Justification & Persistence**:
   - Formulates explainable string:
     > "Computed priority is HIGH (score: 0.65). Highest severity across 1 evidence items is HIGH. Safety risk was NOT DETECTED. Persistence score is 0.10."
   - Upserts `Priority` model attached 1-to-1 to `Incident`.
   - Emits `IncidentEvent(event_type=EventType.PRIORITY_COMPUTED)` with factor breakdown in `payload`.

---

## FLOW 4: SLA Clock Initialization & Poller Evaluation

Initializes the resolution deadline based on Authority SLA rules and advances the accountability state machine.

### Step-by-Step Execution Path:
1. **SLA Start (`app/services/sla_service.py::start_sla`)**:
   - Validates that both `incident.authority` and `incident.priority.final_priority` exist.
   - Reads authority SLA tier duration:
     - Critical: `authority.sla_hours_critical` (default 4h)
     - High: `authority.sla_hours_high` (default 24h)
     - Medium: `authority.sla_hours_medium` (default 72h)
     - Low: `authority.sla_hours_low` (default 168h)
   - Sets `started_at = now()`, `due_at = started_at + timedelta(hours=hours)`.
   - Sets initial SLA state = `AccountabilityState.PENDING`.
   - Transitions incident status from `DRAFT` to `ACTIVE`.
   - Emits `IncidentEvent(event_type=EventType.SLA_STARTED)`.
2. **Background Poller Loop (`app/main.py::run_sla_poller_loop`)**:
   - Executes in the background every 300 seconds (5 minutes).
   - Instantiates `SLAPoller(session)`.
3. **Batch Query & State Evaluation (`app/services/sla_poller.py`)**:
   - Queries all incidents where status in `[ACTIVE, UNDER_REVIEW]` and SLA state is not terminal (`RESOLVED` or `ESCALATION_ELIGIBLE`).
   - For each active incident, invokes `AccountabilityService.evaluate_sla(incident_id, current_time)`:
     - **PENDING → DUE**: If `0 < (due_at - now) <= 24 hours`.
     - **PENDING / DUE → OVERDUE**: If `now >= due_at`. Sets `sla.overdue_at = now`.
     - **OVERDUE → ESCALATION_ELIGIBLE**: If `now >= due_at + 72 hours`. Sets `sla.escalated_at = now`, `is_escalation_eligible = True`.
   - Any transition emits `SLA_STATE_CHANGED` or `ESCALATION_TRIGGERED` timeline events.

---

## FLOW 5: Resolution Submission & Automatic Evaluation (Phase 5 Stages 1 & 2)

An authority submits resolution proof, moving the incident to `UNDER_REVIEW`, followed by automated advisory evaluation.

### Step-by-Step Execution Path:
1. **Submission Interaction (`VerificationPage.jsx`)**:
   - Authority selects an incident, enters repair description in the "Submit Resolution Evidence" box, and clicks "Submit Resolution Proof".
2. **API Request**:
   - `submitResolutionEvidence(incident_id, { description, evidence_type: 'text' })` sends `POST /api/v1/incidents/{id}/submit-resolution`.
3. **Service Logic (`VerificationService.submit_resolution`)**:
   - Guard: Verifies incident is `ACTIVE`. Rejects `CLOSED`, `INVALID`, `RESOLVED`, or `UNDER_REVIEW` with 409 Conflict.
   - Inserts `Evidence` record with `is_verification_evidence = True`, `status = EvidenceStatus.PENDING`.
   - Transitions `incident.status = IncidentStatus.UNDER_REVIEW`.
   - Appends `EVIDENCE_SUBMITTED` and `VERIFICATION_SUBMITTED` events.
   - Flushes transaction.
4. **Advisory Automatic Evaluation (`VerificationService.verify_resolution`)**:
   - Authority or system triggers `POST /api/v1/incidents/{id}/verify-resolution`.
   - Service segregates evidence into `before_ev` (`is_verification_evidence=False`) and `after_ev` (`is_verification_evidence=True`).
   - Determines original severity from `incident.priority` or `before_ev`.
   - Evaluates `after_ev`:
     - If no after evidence or all ambiguous: `INSUFFICIENT_EVIDENCE`.
     - If after severity >= original severity: `UNRESOLVED`.
     - If after severity improved but > 0: `PARTIALLY_RESOLVED`.
     - If after severity is 0 / "none" and matches issue type: `FULLY_RESOLVED`.
   - Upserts `VerificationRecord` with `verified_by = "system"`, confidence, and explanation.
   - Emits `VERIFICATION_RESULT_SET` event (`actor="system"`).
   - **CRITICAL**: Incident status is **NOT** changed. It remains `UNDER_REVIEW`.

---

## FLOW 6: Human Verification Decision (Phase 5 Stage 3)

A human authority reviewer examines the evidence and makes an explicit, binding determination.

### Step-by-Step Execution Path:
1. **Reviewer Action (`VerificationPage.jsx`)**:
   - Reviewer inspects before/after photos and auto-eval summary.
   - Selects decision dropdown: `FULLY_RESOLVED`, `PARTIALLY_RESOLVED`, `UNRESOLVED`, or `INSUFFICIENT_EVIDENCE`.
   - Enters notes and clicks "Confirm Human Decision".
2. **API Request**:
   - `humanVerifyResolution(id, { result, explanation, verified_by: "demo-authority-reviewer" })` calls `POST /api/v1/incidents/{id}/human-verify`.
3. **Backend Guards (`VerificationService.human_verify`)**:
   - Guard 1: Incident status must be `UNDER_REVIEW`.
   - Guard 2: Resolution evidence (`is_verification_evidence = True`) must exist. Rejects approval without evidence.
4. **State Transitions**:
   - `result == FULLY_RESOLVED`:
     - `incident.status = IncidentStatus.RESOLVED`.
     - `incident.sla.state = AccountabilityState.RESOLVED`.
     - `incident.sla.resolved_at = now()`.
   - `result in [INSUFFICIENT_EVIDENCE, UNRESOLVED]`:
     - `incident.status = IncidentStatus.ACTIVE` (returns issue to active authority queue).
   - `result == PARTIALLY_RESOLVED`:
     - `incident.status` remains `UNDER_REVIEW` (more evidence required; cannot close).
5. **Audit Record**:
   - Updates `VerificationRecord` with `verified_by = reviewer`, `confidence = 1.0`.
   - Emits `VERIFICATION_RESULT_SET` timeline event with `actor = reviewer`.
   - Flushes session; committed on request finish.

---

## FLOW 7: Explicit Closure (Phase 5 Stage 4)

Freezes the lifecycle of a verified incident.

### Step-by-Step Execution Path:
1. **Reviewer Action (`VerificationPage.jsx`)**:
   - Once an incident reaches `RESOLVED` status, the green "Close Incident" button becomes active.
   - Clicking it invokes `closeIncident(currentInc.id)`.
2. **API Request**:
   - Calls `POST /api/v1/incidents/{id}/close`.
3. **Backend Guards (`IncidentService.close_incident`)**:
   - Guard: Checks `incident.status == IncidentStatus.RESOLVED`.
   - If already `CLOSED`, returns as-is (idempotent).
   - If `ACTIVE`, `UNDER_REVIEW`, `DRAFT`, or `INVALID`, raises `ConflictError` (409).
4. **State Transition**:
   - `incident.status = IncidentStatus.CLOSED`.
   - Records `IncidentEvent(event_type=EventType.INCIDENT_STATUS_CHANGED, actor="authority", summary="Incident closed after verified resolution.")`.
   - Flushes session.

---

## FLOW 8: Citizen Resolution Proof Visualization

Citizens independently track their filed report and view verified proof of resolution.

### Step-by-Step Execution Path:
1. **Lookup (`CitizenTrackPage.jsx`)**:
   - Citizen enters their incident UUID or reference number into the search bar, or arrives via `/citizen/track?id=<UUID>`.
2. **API Data Fetching**:
   - Fetches incident details via `GET /api/v1/incidents/{id}`.
   - Fetches timeline events via `GET /api/v1/incidents/{id}/timeline`.
3. **Rendering Real Backend Data**:
   - **Status Badge**: Renders real `incident.status` (`ACTIVE`, `UNDER_REVIEW`, `RESOLVED`, `CLOSED`).
   - **Responsible Authority**: Displays assigned `incident.authority.name`, department, and `incident.sla.state` (with countdown and breach warning if overdue).
   - **Lifecycle Timeline**: Maps database `IncidentEvent` rows to visual stepper checkpoints:
     1. Report Submitted (`INCIDENT_CREATED`)
     2. Assigned to Authority (`AUTHORITY_ASSIGNED`)
     3. Under Review / Working (`VERIFICATION_SUBMITTED`)
     4. Resolution Verified (`VERIFICATION_RESULT_SET`)
     5. Case Closed (`INCIDENT_STATUS_CHANGED` to closed)
   - **Resolution Verification Card**:
     - When `incident.verification` exists, renders verification outcome (`FULLY_RESOLVED`, etc.), AI/Human explanation, confidence percentage, and before/after photo comparison containers.

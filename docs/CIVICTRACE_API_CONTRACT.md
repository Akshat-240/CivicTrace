# CivicTrace — API Contract Map & Specification

This document details the complete contract mapping between the React Web Frontend (`apps/web/src/services/api.js` and page components) and the FastAPI Backend (`apps/api/app/api/routes/`).

---

## 1. Complete API Contract Mapping Table

| Frontend File / Caller | Frontend Function | Method | HTTP Endpoint | Request Body / Params | Backend Route Handler | Service Invoked | Response Schema / Type | Integration Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `api.js`<br>`DashboardPage.jsx`<br>`IncidentsPage.jsx`<br>`VerificationPage.jsx`<br>`CitizenHistoryPage.jsx` | `getIncidents(skip, limit)` | `GET` | `/api/v1/incidents` | Query: `skip` (int, default=0), `limit` (int, default=20) | `incidents.py::list_incidents` | `IncidentService.list_incidents()` | `PaginatedResponse[IncidentListItem]` | **PASS** |
| `api.js`<br>`DashboardPage.jsx`<br>`CitizenTrackPage.jsx` | `getIncident(id)` | `GET` | `/api/v1/incidents/{incident_id}` | Path: `incident_id` (UUID) | `incidents.py::get_incident` | `IncidentService.get_incident()` | `IncidentDetail` | **PASS** |
| `api.js`<br>`CitizenReportPage.jsx` | `createIncident(data)` | `POST` | `/api/v1/incidents` | Body: `IncidentSubmit`<br>`{title, description, issue_type, location}` | `incidents.py::create_incident` | `IncidentService.create_incident()` | `IncidentDetail` (HTTP 201) | **PASS** |
| `api.js` | `addIncidentEvidence(id, data)` | `POST` | `/api/v1/incidents/{incident_id}/evidence` | Path: `incident_id` (UUID)<br>Body: `EvidenceSubmit` | `incidents.py::add_evidence` | `EvidenceService.add_evidence()` | `EvidenceResponse` (HTTP 201) | **PASS** (Exported in `api.js`, unused by UI) |
| `api.js`<br>`VerificationPage.jsx` | `getIncidentEvidence(id)` | `GET` | `/api/v1/incidents/{incident_id}/evidence` | Path: `incident_id` (UUID) | `incidents.py::list_evidence` | `EvidenceService.list_evidence()` | `list[EvidenceResponse]` | **PASS** |
| `api.js`<br>`CitizenTrackPage.jsx` | `getIncidentTimeline(id)` | `GET` | `/api/v1/incidents/{incident_id}/timeline` | Path: `incident_id` (UUID) | `incidents.py::get_timeline` | `IncidentService.get_incident_timeline()` | `list[EventResponse]` | **PASS** |
| `api.js` | `getIncidentAccountability(id)` | `GET` | `/api/v1/incidents/{incident_id}/accountability` | Path: `incident_id` (UUID) | `incidents.py::get_accountability` | `IncidentService.get_incident_accountability()` | `SLAResponse` | **PASS** (Exported in `api.js`, UI reads embedded `incident.sla`) |
| `api.js` | `getIncidentVerification(id)` | `GET` | `/api/v1/incidents/{incident_id}/verification` | Path: `incident_id` (UUID) | `incidents.py::get_verification` | `IncidentService.get_incident_verification()` | `VerificationResponse` | **PASS** (Exported in `api.js`, UI reads embedded `incident.verification`) |
| None (Internal route) | None | `POST` | `/api/v1/incidents/{incident_id}/evidence/{evidence_id}/analyze` | Path: `incident_id` (UUID), `evidence_id` (UUID) | `incidents.py::analyze_evidence` | `AIService.process_evidence()` | `AIAnalysisResult` | **UNUSED** (Backend only; no frontend caller) |
| `api.js` | `assignJurisdiction(id)` | `POST` | `/api/v1/incidents/{incident_id}/assign-jurisdiction` | Path: `incident_id` (UUID) | `incidents.py::assign_jurisdiction` | `IncidentService.assign_jurisdiction()` | `IncidentDetail` | **PASS** (Orchestrated internally by backend `create_incident`) |
| `api.js` | `prioritizeIncident(id)` | `POST` | `/api/v1/incidents/{incident_id}/prioritize` | Path: `incident_id` (UUID) | `incidents.py::compute_priority` | `PriorityService.compute_priority()` | `dict` (Priority output) | **PASS** (Orchestrated internally by backend `create_incident`) |
| `api.js` | `startIncidentSLA(id)` | `POST` | `/api/v1/incidents/{incident_id}/start-sla` | Path: `incident_id` (UUID) | `incidents.py::start_sla` | `AccountabilityService.start_sla()` | `dict` (SLA record fields) | **PASS** (Orchestrated internally by backend `create_incident`) |
| `api.js` | `evaluateIncidentSLA(id)` | `POST` | `/api/v1/incidents/{incident_id}/evaluate-sla` | Path: `incident_id` (UUID) | `incidents.py::evaluate_sla` | `AccountabilityService.evaluate_sla()` | `dict` (SLA record fields) | **PASS** (Handled in background by `SLAPoller`) |
| `api.js`<br>`VerificationPage.jsx` | `submitResolutionEvidence(id, data)` | `POST` | `/api/v1/incidents/{incident_id}/submit-resolution` | Path: `incident_id` (UUID)<br>Body: `ResolutionSubmit`<br>`{description, evidence_type}` | `incidents.py::submit_resolution` | `VerificationService.submit_resolution()` | `EvidenceResponse` (HTTP 201) | **PASS** (Transitions `ACTIVE` → `UNDER_REVIEW`) |
| `api.js`<br>`VerificationPage.jsx` | `verifyResolution(id)` | `POST` | `/api/v1/incidents/{incident_id}/verify-resolution` | Path: `incident_id` (UUID) | `incidents.py::verify_resolution` | `VerificationService.verify_resolution()` | `dict` (`result`, `explanation`, `confidence`, `verified_at`) | **PASS** (Automatic advisory eval; does NOT change incident status) |
| `api.js`<br>`VerificationPage.jsx` | `humanVerifyResolution(id, data)` | `POST` | `/api/v1/incidents/{incident_id}/human-verify` | Path: `incident_id` (UUID)<br>Body: `VerificationSubmit`<br>`{result, explanation, verified_by}` | `incidents.py::human_verify` | `VerificationService.human_verify()` | `VerificationResponse` | **PASS** (`FULLY_RESOLVED` → `RESOLVED`; `UNRESOLVED` → `ACTIVE`) |
| `api.js`<br>`VerificationPage.jsx` | `closeIncident(id)` | `POST` | `/api/v1/incidents/{incident_id}/close` | Path: `incident_id` (UUID) | `incidents.py::close_incident` | `IncidentService.close_incident()` | `IncidentDetail` | **PASS** (Guarded: only `RESOLVED` → `CLOSED`) |
| None (Internal route) | None | `POST` | `/api/v1/system/evaluate-slas` | None | `system.py::evaluate_slas` | `SLAPoller.evaluate_all_active_slas()` | `dict` (`message`, `summary`) | **UNUSED** (Backend only; polled via background task) |
| None | None | `GET` | `/health` | None | `health.py::health_check` | None | `HealthResponse` (`status="ok"`) | **PASS** |
| None | None | `GET` | `/api/v1/gis/jurisdiction` | Query: `latitude`, `longitude` | `gis.py::resolve_jurisdiction` | `GISService.resolve_jurisdiction()` | `JurisdictionResult` | **BROKEN / UNMOUNTED** (`gis.py` router not included in `main.py`) |
| None | None | `*` | `/api/v1/evidence/*` | None | `evidence.py` | None | None | **DEAD CODE / PLACEHOLDER** (Placeholder file) |
| None | None | `*` | `/api/v1/accountability/*` | None | `accountability.py` | None | None | **DEAD CODE / PLACEHOLDER** (Placeholder file) |
| None | None | `*` | `/api/v1/verification/*` | None | `verification.py` | None | None | **DEAD CODE / PLACEHOLDER** (Placeholder file) |

---

## 2. Request and Response Envelopes

### Base Error Envelope (HTTP 4xx / 5xx)
All route errors and unhandled exceptions are translated into this schema:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Incident 61c6d93e-889d-42fc-b6b9-b167ce631d47 not found.",
    "detail": null
  }
}
```

### Standard List Envelope (HTTP 200)
Paginated list endpoints return data wrapped in `PaginatedResponse`:
```json
{
  "data": [
    {
      "id": "c6e2729b-0055-4b80-8d9a-689263bda5b7",
      "created_at": "2026-09-14T12:00:00Z",
      "updated_at": "2026-09-14T12:00:00Z",
      "reference_number": "INC-A1B2C3D4",
      "status": "active",
      "issue_type": "pothole",
      "title": "Road Damage Issue",
      "evidence_count": 1,
      "ai_ambiguity_flag": false,
      "location": {
        "id": "11111111-2222-3333-4444-555555555555",
        "created_at": "2026-09-14T12:00:00Z",
        "updated_at": "2026-09-14T12:00:00Z",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "address_raw": "MG Road, Near Hazratganj Crossing"
      },
      "authority": {
        "id": "61c6d93e-889d-42fc-b6b9-b167ce631d47",
        "name": "Lucknow Municipal Corporation",
        "short_code": "LMC",
        "is_active": true,
        "sla_hours_low": 168,
        "sla_hours_medium": 72,
        "sla_hours_high": 24,
        "sla_hours_critical": 4
      },
      "priority_level": "high",
      "accountability_state": "pending"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## 3. Detailed Endpoint Contracts

### `POST /api/v1/incidents`
- **Purpose**: Creates a new incident from citizen input.
- **Side Effect**: Automatically triggers GIS jurisdiction resolution, Priority computation, and SLA start.
- **Status**: 201 Created
- **Request Body**:
  ```json
  {
    "title": "Large pothole on MG Road",
    "description": "Deep pothole causing vehicular damage.",
    "issue_type": "pothole",
    "location": {
      "latitude": 26.8467,
      "longitude": 80.9462,
      "address_raw": "MG Road, Hazratganj",
      "accuracy_meters": 10.0
    }
  }
  ```
- **Response**: Full `IncidentDetail` schema.

### `POST /api/v1/incidents/{id}/submit-resolution`
- **Purpose**: Authority reports work completion with proof.
- **Guards**: Incident status must be `ACTIVE`. Rejects `CLOSED`, `INVALID`, `RESOLVED`, `UNDER_REVIEW` with 409 Conflict.
- **Side Effect**: Ingests evidence with `is_verification_evidence = true`. Transitions status to `UNDER_REVIEW`. Appends `EVIDENCE_SUBMITTED` and `VERIFICATION_SUBMITTED` events.
- **Request Body**:
  ```json
  {
    "description": "Asphalt patching completed and compacted by Road Team 04.",
    "evidence_type": "text"
  }
  ```
- **Response**: `EvidenceResponse` (HTTP 201 Created).

### `POST /api/v1/incidents/{id}/verify-resolution`
- **Purpose**: Runs automated evidence evaluation comparing before/after perception.
- **Guards**: Incident cannot be in `CLOSED` or `INVALID` state.
- **Side Effect**: Creates/updates `VerificationRecord`. verified_by = `"system"`. **Does NOT alter incident status.**
- **Response**:
  ```json
  {
    "result": "fully_resolved",
    "explanation": "Evidence supports complete resolution of the issue.",
    "confidence": 0.9,
    "verified_at": "2026-09-14T12:30:00Z"
  }
  ```

### `POST /api/v1/incidents/{id}/human-verify`
- **Purpose**: Human reviewer evaluates evidence and issues binding state transition.
- **Guards**:
  1. Incident status must be `UNDER_REVIEW`.
  2. Resolution evidence (`is_verification_evidence = true`) must exist.
- **Status Transitions**:
  - `result: "fully_resolved"` → Incident status = `RESOLVED`, SLA state = `RESOLVED`.
  - `result: "insufficient_evidence"` → Incident status = `ACTIVE`.
  - `result: "unresolved"` → Incident status = `ACTIVE`.
  - `result: "partially_resolved"` → Incident status remains `UNDER_REVIEW`.
- **Request Body**:
  ```json
  {
    "result": "fully_resolved",
    "explanation": "Reviewed photo and repair log. Issue fully rectified.",
    "verified_by": "demo-authority-reviewer"
  }
  ```
- **Response**: `VerificationResponse` (HTTP 200 OK).

### `POST /api/v1/incidents/{id}/close`
- **Purpose**: Closes a verified incident.
- **Guards**: Incident status must be `RESOLVED`. Any other status (`ACTIVE`, `UNDER_REVIEW`, `DRAFT`, `INVALID`) is rejected with 409 Conflict. Calling on `CLOSED` is idempotent.
- **Side Effect**: Incident status = `CLOSED`. Appends `INCIDENT_STATUS_CHANGED` event (`actor="authority"`).
- **Response**: `IncidentDetail` (HTTP 200 OK).

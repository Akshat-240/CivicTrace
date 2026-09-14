# CivicTrace — Developer Learning Guide & Architectural Rationales

This guide provides a structured, step-by-step reading roadmap for onboarding new software engineers to the CivicTrace codebase, followed by an in-depth architectural rationale explaining why files are partitioned the way they are.

---

## 1. Architectural Learning Roadmap

Do not read this repository alphabetically. Follow this dependency-ordered progression to build an accurate mental model of the system from foundational contracts up to user interfaces.

```
1. Configuration & Enums (Core Domain Primitives)
   └── app/core/config.py ──> app/models/enums.py
2. Foundational Database Models
   └── app/models/location.py ──> app/models/authority.py ──> app/models/jurisdiction.py ──> app/models/incident.py
3. Dependent Companion Models
   └── app/models/evidence.py ──> app/models/priority.py ──> app/models/sla.py ──> app/models/verification.py ──> app/models/event.py
4. Ingestion & Spatial Services
   └── app/services/gis_service.py ──> app/services/priority_service.py ──> app/services/sla_service.py
5. Orchestration & Core Workflows
   └── app/services/incident_service.py ──> app/services/verification_service.py ──> app/services/sla_poller.py
6. API Layer & Transport
   └── app/schemas/ ──> app/api/routes/incidents.py ──> app/main.py
7. Frontend Integration
   └── apps/web/src/services/api.js ──> CitizenReportPage ──> CitizenTrackPage ──> DashboardPage ──> VerificationPage
```

---

### Step 1: Configuration & Domain Primitives
- **Files**: `apps/api/app/core/config.py` → `apps/api/app/models/enums.py`
- **Why Learn Now?**: You cannot understand system logic without knowing the controlled vocabulary (enums) and operational settings (database URL, SLA configurations, log levels).
- **What to Understand**:
  - `IncidentStatus`: `DRAFT`, `ACTIVE`, `UNDER_REVIEW`, `RESOLVED`, `CLOSED`, `INVALID`.
  - `AccountabilityState`: `PENDING`, `DUE`, `OVERDUE`, `ESCALATION_ELIGIBLE`, `RESOLVED`.
  - `VerificationResult`: `FULLY_RESOLVED`, `PARTIALLY_RESOLVED`, `UNRESOLVED`, `INSUFFICIENT_EVIDENCE`.
  - Enums are pure data string enums — they contain no logic.
- **Next**: Step 2 (Entity Models).

---

### Step 2: Foundational Spatial & Relational Models
- **Files**: `app/models/location.py` → `app/models/authority.py` → `app/models/jurisdiction.py` → `app/models/incident.py`
- **Why Learn Now?**: Understand the core relational triangle of CivicTrace: Location, Jurisdiction, and Authority, and how Incident binds them together.
- **What to Understand**:
  - `Location` is a standalone entity carrying PostGIS Point geometry (`geom`) and redundant coordinate floats.
  - `Jurisdiction` carries a PostGIS MultiPolygon boundary (`boundary`) and belongs to an `Authority`.
  - `ck_incidents_jurisdiction_authority_invariant` in `incident.py` prevents orphan authority assignments.
- **Next**: Step 3 (Companion Models).

---

### Step 3: Dependent Domain Models
- **Files**: `app/models/evidence.py` → `app/models/priority.py` → `app/models/sla.py` → `app/models/verification.py` → `app/models/event.py`
- **Why Learn Now?**: Learn how single responsibilities are isolated into 1-to-1 companion records and append-only audit tables.
- **What to Understand**:
  - `Evidence` is the atomic input unit; `is_verification_evidence` flags resolution proof.
  - `Priority` and `SLA` isolate computational scoring and timer states from the generic incident row.
  - `VerificationRecord` holds before/after evidence references and reviewer decisions.
  - `IncidentEvent` is an append-only timeline preserving the complete audit history.
- **Next**: Step 4 (Domain Calculation Engines).

---

### Step 4: Specialized Domain Engines
- **Files**: `app/services/gis_service.py` → `app/services/priority_service.py` → `app/services/sla_service.py`
- **Why Learn Now?**: These three services form the deterministic core of CivicTrace. They have no AI dependencies and execute strict business mathematics.
- **What to Understand**:
  - `GISService`: Uses PostGIS `ST_Contains` for spatial containment. Rejects ambiguity with `JURISDICTION_CONFLICT`. Never guesses.
  - `PriorityService`: Computes `(Severity * 0.5) + (Safety * 0.3) + (Persistence * 0.2)` and maps to discrete priority tiers.
  - `AccountabilityService`: Computes deadlines from authority SLA windows and advances linear states (`PENDING` → `DUE` → `OVERDUE` → `ESCALATION_ELIGIBLE`).
- **Next**: Step 5 (Orchestration & Verification).

---

### Step 5: Orchestration & Phase 5 Verification
- **Files**: `app/services/incident_service.py` → `app/services/verification_service.py` → `app/services/sla_poller.py`
- **Why Learn Now?**: This is where domain engines are orchestrated into operational workflows, including the complete Phase 5 4-stage lifecycle.
- **What to Understand**:
  - `IncidentService.create_incident`: Orchestrates GIS assignment, priority scoring, and SLA launch on submission.
  - `VerificationService`:
    - Stage 1: `submit_resolution` (Ingests proof, moves `ACTIVE` → `UNDER_REVIEW`).
    - Stage 2: `verify_resolution` (Advisory auto-eval, verified_by `"system"`, **no status change**).
    - Stage 3: `human_verify` (Binding reviewer decision; only `FULLY_RESOLVED` moves to `RESOLVED`).
  - `IncidentService.close_incident`: Stage 4 (Guarded: only `RESOLVED` → `CLOSED`).
- **Next**: Step 6 (API Layer).

---

### Step 6: API Layer & Contracts
- **Files**: `app/schemas/` → `app/api/routes/incidents.py` → `app/main.py`
- **Why Learn Now?**: Understand how HTTP requests are validated via Pydantic schemas, routed to services, and wrapped in transactional database sessions.
- **What to Understand**:
  - `get_db` dependency in `database.py` manages request-level transactions (commit on success, rollback on error).
  - Schema separation between create, submit, list, and detail representations.
  - Startup lifespan initializes the database check and launches the background `SLAPoller` task.
- **Next**: Step 7 (Frontend Integration).

---

### Step 7: Frontend Integration & Portals
- **Files**: `apps/web/src/services/api.js` → `CitizenReportPage.jsx` → `CitizenTrackPage.jsx` → `DashboardPage.jsx` → `VerificationPage.jsx`
- **Why Learn Now?**: See how the web interface renders backend state, triggers actions, and where prototype boundaries exist.
- **What to Understand**:
  - `api.js` is the central fetch wrapper handling all communication with `/api/v1`.
  - `CitizenReportPage.jsx` and `CitizenTrackPage.jsx` consume and display real backend state.
  - `VerificationPage.jsx` implements the full 4-stage UI for authority reviewers.
  - The Admin portal and citizen feedback pages are prototype scaffolding backed by `mockData.js`.

---

## 2. "Why Was This File Created?" — Architectural Separation Rationales

### 1. Why does `gis_service.py` exist separately from `incident_service.py`?
- **Separation of Spatial Computing from Orchestration**: GIS operations require spatial geometry algorithms (`ST_Contains`), spatial reference system transformations (SRID 4326), and administrative boundary collision detection. Mixing spatial algorithms into generic CRUD workflows creates high coupling and makes spatial queries difficult to test in isolation.
- **Single Responsibility**: `GISService` has one job: given coordinates $(x, y)$, return the administrative boundary. It does not care about incident priority, status, or reporting users.

### 2. Why does `verification_service.py` exist separately from `evidence_service.py`?
- **Ingestion vs. Adjudication**: `evidence_service.py` is responsible for raw input handling (uploading metadata, linking media to an incident). `verification_service.py` represents the core business differentiator of CivicTrace: the adjudication of claims.
- **Complex Multi-Stage Workflow**: Verification involves evaluating comparative evidence (before vs. after), running advisory heuristic models, recording human reviewer identities, and driving lifecycle state transitions. Keeping this separate ensures that evidence ingestion remains a simple, append-only operation.

### 3. Why do `schemas/` exist separately from `models/`?
- **Decoupling Transport from Persistence**: SQLAlchemy `models/` define relational database tables, foreign keys, and indexes. Pydantic `schemas/` define external API network contracts.
- **Information Hiding & Over-Posting Prevention**: The database requires internal columns (`id`, `created_at`, `storage_key`, WKB geometry), while API consumers need clean coordinates or specific subset views (e.g. `IncidentListItem` omits large nested relations to optimize list performance). Exposing ORM models directly to HTTP routes is a security and performance antipattern.

### 4. Why does `api.js` exist instead of calling `fetch()` directly in React components?
- **Unified Network Error Handling**: All HTTP responses pass through `fetchAPI()`, which parses standard backend error envelopes (`{ error: { code, message } }`) and normalizes network failures.
- **Endpoint Decoupling**: If an API route path changes (e.g., from `/incidents/{id}/submit-resolution` to `/incidents/{id}/resolution`), only `api.js` needs modification rather than hunting through multiple UI components.

### 5. Why does `IncidentEvent` exist instead of relying solely on `Incident.status`?
- **Accountability Requires Audit Provenance**: An incident status column only tells you where an incident is *now*. It cannot tell you:
  - Who assigned the priority and why.
  - When an SLA breached and who was notified.
  - What the automated evaluation confidence was before a human reviewer made a decision.
- **Append-Only Immutability**: `IncidentEvent` is configured with `ON DELETE RESTRICT`. It creates a tamper-resistant forensic log of every state change in the civic issue lifecycle.

### 6. Why are `Priority` and `SLA` separate 1-to-1 tables instead of columns on `incidents`?
- **Domain Normalization & Lifecycle Independence**:
  - `Priority` has its own complex calculation factors (`severity`, `safety_risk`, `persistence_score`, `explanation`) which are updated when new evidence arrives.
  - `SLA` is an active state machine that ticks independently of incident content (`started_at`, `due_at`, `overdue_at`, `escalated_at`, `is_escalation_eligible`).
  - Separating them avoids "god table" bloat on `incidents`, allows independent indexing (e.g., indexing `ix_slas_state_due_at` for high-speed background poller scans), and keeps domain concerns cleanly partitioned.

### 7. Why is `Location` a separate table instead of float columns on `incidents`?
- **Spatial Multi-Tenancy**: A single geographic location can be referenced by both an `Incident` and individual `Evidence` items independently.
- **PostGIS Indexing & Geocoding**: Housing the spatial geometry (`geom`), reverse-geocoded street names, suburbs, wards, and accuracy radii in a dedicated entity allows PostGIS spatial indexes (GIST) to operate efficiently without loading full incident records.

### 8. Why does `SLAPoller` exist separately from `AccountabilityService`?
- **Batch Infrastructure vs. Business Logic**: `AccountabilityService.evaluate_sla()` contains the pure mathematical and state machine rules for evaluating a single incident's SLA against a clock. `SLAPoller` handles execution infrastructure: querying candidate batches, iterating over IDs, handling per-incident rollbacks, and generating summary metrics for background task execution.

# CivicTrace — Complete Repository File Inventory

This inventory provides a comprehensive audit of all files across the CivicTrace repository, categorizing them by layer, business purpose, runtime utilization, dependencies, and lifecycle status.

---

## 1. Inventory Summary by Category

| Category | File Count | Description |
| :--- | :--- | :--- |
| **Backend Core & Application** | 8 | Application entrypoint, logging, database configuration, security, error handling |
| **Backend Domain Models** | 11 | SQLAlchemy ORM declarative models, enums, constraints, PostGIS bindings |
| **Backend Schemas** | 10 | Pydantic v2 schemas for request validation and response serialization |
| **Backend Repositories** | 4 | Data access layer isolating queries from domain business logic |
| **Backend Domain Services** | 11 | Core business logic (GIS, Priority, SLA, SLA Poller, Fusion, Verification, AI) |
| **Backend API Routes** | 8 | FastAPI route controllers, dependencies, and endpoints |
| **Database Migrations** | 6 | Alembic migration scripts, env configuration, and script templates |
| **Backend Test Suite** | 17 | Pytest automated test suites covering unit, integration, and E2E scenarios |
| **Backend Scratch / Debug Scripts** | 10 | Ad-hoc development and diagnostic scripts located in `apps/api/` |
| **Frontend Core & Infrastructure** | 6 | Vite entrypoint, HTML template, global CSS, root App component, routes |
| **Frontend Shared Components** | 14 | Reusable UI components (Modals, Badges, Headers, Navigation Sidebars, Layouts) |
| **Frontend Portal Pages** | 18 | Citizen portal (6), Authority portal (6), Admin portal (9 - incl. detail) |
| **Frontend Services & Data** | 2 | REST API client (`api.js`) and Mock dataset (`mockData.js`) |
| **Repository Root Scripts & Seed** | 22 | Database seeder (`temp_seed.py`), setup scripts, browser verification scripts |
| **Repository Root Config & Docs** | 14 | Docker configs, package manifests, contracts, architecture documentation |

---

## 2. Exhaustive File Inventory Table

| File Path | Layer | Purpose | Runtime Used? | Key Dependencies | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `apps/api/app/main.py` | Backend Application | Application factory, middleware registration, background task lifecycle, exception routing | **Yes** | FastAPI, CORS, Database Engine, Route Routers, SLAPoller | Core Production |
| `apps/api/app/core/config.py` | Backend Core | Application settings loaded from `.env` via `pydantic-settings` | **Yes** | `pydantic-settings` | Core Production |
| `apps/api/app/core/database.py` | Backend Core | Async SQLAlchemy engine, session maker, base ORM model (`Base`), DB health check | **Yes** | SQLAlchemy, asyncpg, psycopg | Core Production |
| `apps/api/app/core/errors.py` | Backend Core | Domain exception hierarchy (`CivicTraceError`) and FastAPI global exception handlers | **Yes** | FastAPI, structlog | Core Production |
| `apps/api/app/core/logging.py` | Backend Core | Structured JSON / console logger configuration using `structlog` | **Yes** | structlog, logging | Core Production |
| `apps/api/app/core/security.py` | Backend Core | JWT generation/decoding and bcrypt password hashing utilities | **No** (Unused by routes) | python-jose, passlib | Partial / Scaffolding |
| `apps/api/app/api/dependencies.py` | Backend API | Dependency injection providers (`get_db`, `get_settings`) | **Yes** | FastAPI Depends, Database Session | Core Production |
| `apps/api/app/api/routes/__init__.py` | Backend API | Routes package init file | **Yes** | None | Core Production |
| `apps/api/app/api/routes/incidents.py` | Backend API | Core REST API routes for incidents, evidence, timeline, SLA, GIS, and verification | **Yes** | IncidentService, EvidenceService, VerificationService, AIService | Core Production |
| `apps/api/app/api/routes/system.py` | Backend API | System maintenance endpoint (`POST /api/v1/system/evaluate-slas`) | **Yes** | SLAPoller | Core Production |
| `apps/api/app/api/routes/health.py` | Backend API | Liveness probe endpoint (`GET /health`) | **Yes** | FastAPI APIRouter | Core Production |
| `apps/api/app/api/routes/gis.py` | Backend API | Standalone GIS endpoint (`GET /api/v1/gis/jurisdiction`) | **No** (Not mounted in `main.py`) | GISService, DbSession | Unmounted Route |
| `apps/api/app/api/routes/evidence.py` | Backend API | Placeholder route for standalone evidence endpoints | **No** | FastAPI APIRouter | Obsolete Placeholder |
| `apps/api/app/api/routes/accountability.py` | Backend API | Placeholder route for standalone SLA endpoints | **No** | FastAPI APIRouter | Obsolete Placeholder |
| `apps/api/app/api/routes/verification.py` | Backend API | Placeholder route for standalone verification endpoints | **No** | FastAPI APIRouter | Obsolete Placeholder |
| `apps/api/app/models/__init__.py` | Backend Models | Re-exports all SQLAlchemy models for Alembic discovery | **Yes** | All model modules | Core Production |
| `apps/api/app/models/enums.py` | Backend Models | Controlled string enum vocabulary for domain states and classifications | **Yes** | enum | Core Production |
| `apps/api/app/models/incident.py` | Backend Models | Canonical `Incident` ORM model, progressive foreign keys, and DB invariants | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/location.py` | Backend Models | First-class `Location` ORM model with PostGIS `Geometry('POINT', 4326)` | **Yes** | GeoAlchemy2, SQLAlchemy | Core Production |
| `apps/api/app/models/jurisdiction.py` | Backend Models | `Jurisdiction` ORM model with PostGIS `Geometry('MULTIPOLYGON', 4326)` | **Yes** | GeoAlchemy2, SQLAlchemy | Core Production |
| `apps/api/app/models/authority.py` | Backend Models | `Authority` ORM model holding SLA tier durations per priority | **Yes** | SQLAlchemy, Base | Core Production |
| `apps/api/app/models/evidence.py` | Backend Models | `Evidence` ORM model holding raw input metadata, AI perception fields, and verification flag | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/priority.py` | Backend Models | 1-to-1 `Priority` ORM model storing factor scores, final priority, and explanation | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/sla.py` | Backend Models | 1-to-1 `SLA` ORM model tracking accountability state progression and timestamps | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/verification.py` | Backend Models | 1-to-1 `VerificationRecord` ORM model storing before/after evidence links, result, and reviewer | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/event.py` | Backend Models | Append-only `IncidentEvent` audit timeline model | **Yes** | SQLAlchemy, Base, Enums | Core Production |
| `apps/api/app/models/asset.py` | Backend Models | `Asset` ORM model for optional infrastructure linking | **Partial** (Seed data only) | SQLAlchemy, Base, Enums | Data Foundation |
| `apps/api/app/repositories/__init__.py` | Backend Repositories | Repositories package init | **Yes** | None | Core Production |
| `apps/api/app/repositories/incident_repo.py` | Backend Repositories | Data access for `Incident` and related eager loads (`selectinload`) | **Yes** | SQLAlchemy select, Incident | Core Production |
| `apps/api/app/repositories/evidence_repo.py` | Backend Repositories | Data access for `Evidence` records | **Yes** | SQLAlchemy select, Evidence | Core Production |
| `apps/api/app/repositories/event_repo.py` | Backend Repositories | Append and query data access for `IncidentEvent` records | **Yes** | SQLAlchemy select, IncidentEvent | Core Production |
| `apps/api/app/schemas/__init__.py` | Backend Schemas | Schemas package init re-exporting public contracts | **Yes** | All schema modules | Core Production |
| `apps/api/app/schemas/base.py` | Backend Schemas | Common base (`CivicBaseModel`), audit fields, pagination, and error envelopes | **Yes** | Pydantic v2 | Core Production |
| `apps/api/app/schemas/incident.py` | Backend Schemas | Incident submit, list, detail, and resolution submission contracts | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/schemas/location.py` | Backend Schemas | Location creation and JSON response contracts (stripping raw WKB) | **Yes** | Pydantic v2 | Core Production |
| `apps/api/app/schemas/jurisdiction.py` | Backend Schemas | Authority and Jurisdiction serialization contracts | **Yes** | Pydantic v2 | Core Production |
| `apps/api/app/schemas/evidence.py` | Backend Schemas | Evidence submission and response contracts | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/schemas/priority.py` | Backend Schemas | Priority, SLA, and Human Verification submission/response contracts | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/schemas/event.py` | Backend Schemas | Incident event timeline serialization contract | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/schemas/gis.py` | Backend Schemas | GIS spatial containment structured result contract | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/schemas/ai.py` | Backend Schemas | Structured AI perception output schema matching Gemini JSON specification | **Yes** | Pydantic v2, Enums | Core Production |
| `apps/api/app/services/__init__.py` | Backend Services | Services package init | **Yes** | None | Core Production |
| `apps/api/app/services/incident_service.py` | Backend Services | Incident orchestration: creation, GIS routing, priority scoring, SLA launch, and closure | **Yes** | Repositories, GIS, Priority, SLA Services | Core Production |
| `apps/api/app/services/evidence_service.py` | Backend Services | Evidence ingestion and listing | **Yes** | Repositories, IncidentService | Core Production |
| `apps/api/app/services/gis_service.py` | Backend Services | PostGIS spatial point-in-polygon containment resolution | **Yes** | PostGIS `ST_Contains`, Jurisdiction | Core Production |
| `apps/api/app/services/priority_service.py` | Backend Services | Deterministic mathematical priority scoring based on severity, safety, persistence | **Yes** | Incident, Priority, PriorityConfig | Core Production |
| `apps/api/app/services/sla_service.py` | Backend Services | SLA deadline computation and linear state machine evaluation | **Yes** | SLA, Incident, Authority, Event | Core Production |
| `apps/api/app/services/sla_poller.py` | Backend Services | Background batch evaluation loop across all active SLAs | **Yes** | SLA, AccountabilityService | Core Production |
| `apps/api/app/services/fusion_service.py` | Backend Services | Spatial & temporal weighted deduplication engine | **No** (Tests only; unwired in API) | PostGIS `ST_DistanceSphere`, Evidence | Backend Complete / Unwired |
| `apps/api/app/services/verification_service.py` | Backend Services | Phase 5 verification engine: resolution submission, auto-eval, human verify | **Yes** | VerificationRecord, Evidence, SLA, Incident | Core Production |
| `apps/api/app/services/ai/base.py` | Backend Services | Abstract base class `AIProvider` interface | **Yes** | abc.ABC | Core Production |
| `apps/api/app/services/ai/gemini.py` | Backend Services | Google Gemini API perception provider with structured schema output & hashing cache | **Yes** | google-genai SDK, Pydantic | Core Production |
| `apps/api/app/services/ai/service.py` | Backend Services | AI orchestration service updating Evidence records with perception attributes | **Yes** | GeminiAIProvider, EvidenceRepository | Core Production |
| `apps/api/alembic/env.py` | Database Migrations | Alembic runtime environment connecting models with Postgres database engine | **Yes** (During migration) | Alembic, SQLAlchemy, Base | Core Production |
| `apps/api/alembic/script.py.mako` | Database Migrations | Alembic migration script template | **Yes** (During migration) | Mako | Core Production |
| `apps/api/alembic/versions/0001_enable_postgis.py` | Database Migrations | Migration 1: Enables `postgis` and `postgis_topology` extensions | **Yes** (Applied) | Alembic op | Applied Migration |
| `apps/api/alembic/versions/0002_domain_foundation.py` | Database Migrations | Migration 2: Creates all 10 core domain relational tables | **Yes** (Applied) | Alembic op, SQLAlchemy | Applied Migration |
| `apps/api/alembic/versions/20260912_0925_43389400dc2b_phase_2_tables.py` | Database Migrations | Migration 3: Index adjustments, unique constraints, and enum alignments | **Yes** (Applied) | Alembic op | Applied Migration |
| `apps/api/alembic/versions/0003_jur_auth_invariant.py` | Database Migrations | Migration 4: Enforces `ck_incidents_jurisdiction_authority_invariant` constraint | **Yes** (Applied) | Alembic op | Applied Migration |
| `apps/api/tests/conftest.py` | Tests | Pytest fixtures: event loop, async HTTP client, test DB session isolation | Test Runner | pytest, pytest-asyncio, httpx | Core Test Fixture |
| `apps/api/tests/test_ai.py` | Tests | Unit tests for AI provider prompt construction and output parsing | Test Runner | pytest | Automated Tests |
| `apps/api/tests/test_api_incidents.py` | Tests | HTTP integration tests for Incident and Evidence endpoints | Test Runner | httpx AsyncClient | Automated Tests |
| `apps/api/tests/test_config.py` | Tests | Tests environment parsing, CORS origin list splitting, and defaults | Test Runner | Settings | Automated Tests |
| `apps/api/tests/test_database.py` | Tests | Verifies DB connection health check and session factory behavior | Test Runner | SQLAlchemy | Automated Tests |
| `apps/api/tests/test_e2e_pipeline.py` | Tests | Full lifecycle test from report creation to resolution | Test Runner | All domain services | Automated Tests |
| `apps/api/tests/test_fusion.py` | Tests | Spatial and temporal incident fusion tests | Test Runner | FusionService | Automated Tests |
| `apps/api/tests/test_gate4_hardening.py` | Tests | Tests database invariant constraint against orphan authority assignments | Test Runner | Incident, Jurisdiction | Automated Tests |
| `apps/api/tests/test_gis.py` | Tests | GIS point-in-polygon containment, conflict, and invalid coordinate tests | Test Runner | GISService | Automated Tests |
| `apps/api/tests/test_health.py` | Tests | Health endpoint HTTP response tests | Test Runner | httpx AsyncClient | Automated Tests |
| `apps/api/tests/test_models.py` | Tests | Table schema, check constraint, and column validation tests | Test Runner | SQLAlchemy Models | Automated Tests |
| `apps/api/tests/test_phase5_e2e.py` | Tests | Phase 5 specific tests: Tests A through N (14 E2E verification scenarios) | Test Runner | VerificationService, IncidentService | Automated Tests |
| `apps/api/tests/test_priority.py` | Tests | Priority Engine mathematical model and boundary threshold tests | Test Runner | PriorityService | Automated Tests |
| `apps/api/tests/test_sla.py` | Tests | SLA window calculation and state transition tests | Test Runner | AccountabilityService | Automated Tests |
| `apps/api/tests/test_sla_poller.py` | Tests | Background SLA poller multi-incident batch execution tests | Test Runner | SLAPoller | Automated Tests |
| `apps/api/tests/test_startup.py` | Tests | FastAPI application creation and routing sanity tests | Test Runner | FastAPI | Automated Tests |
| `apps/api/tests/test_verification.py` | Tests | Evidence-backed resolution evaluation algorithm tests | Test Runner | VerificationService | Automated Tests |
| `apps/web/src/main.jsx` | Frontend Core | React 18 DOM mount and React Router `BrowserRouter` provider | **Yes** | React, ReactDOM, React Router | Core Production |
| `apps/web/src/App.jsx` | Frontend Core | Root application container component mounting `AppRoutes` | **Yes** | AppRoutes | Core Production |
| `apps/web/src/routes/AppRoutes.jsx` | Frontend Core | Application route definitions across Public, Authority, Admin, and Citizen portals | **Yes** | React Router v6 | Core Production |
| `apps/web/src/services/api.js` | Frontend Service | Fetch API wrapper communicating with the FastAPI backend `/api/v1` routes | **Yes** | Native Fetch API | Core Production |
| `apps/web/src/data/mockData.js` | Frontend Data | Synthetic dataset used for Admin Portal, mock statistics, and UI fallbacks | **Yes** (Admin portal) | Static JS objects | Prototype Mock Data |
| `apps/web/src/components/common/PriorityBadge.jsx` | Frontend Component | Visual badge rendering priority level with semantic color classes | **Yes** | React | Core UI Component |
| `apps/web/src/components/common/StatusBadge.jsx` | Frontend Component | Visual badge rendering incident status | **Yes** | React | Core UI Component |
| `apps/web/src/components/common/Modal.jsx` | Frontend Component | Accessible modal dialog for evidence inspection and popups | **Yes** | React | Core UI Component |
| `apps/web/src/components/layout/Header.jsx` | Frontend Component | Top navigation header with portal title, role indicator, and profile icon | **Yes** | React | Core Layout |
| `apps/web/src/components/layout/Sidebar.jsx` | Frontend Component | Authority portal sidebar navigation | **Yes** | React Router NavLink | Core Layout |
| `apps/web/src/components/layout/AuthorityLayout.jsx` | Frontend Component | Layout wrapper for `/authority/*` routes | **Yes** | React Router Outlet | Core Layout |
| `apps/web/src/components/layout/CitizenSidebar.jsx` | Frontend Component | Citizen portal sidebar navigation | **Yes** | React Router NavLink | Core Layout |
| `apps/web/src/components/layout/CitizenLayout.jsx` | Frontend Component | Layout wrapper for `/citizen/*` routes | **Yes** | React Router Outlet | Core Layout |
| `apps/web/src/components/layout/AdminSidebar.jsx` | Frontend Component | Admin portal sidebar navigation | **Yes** | React Router NavLink | Core Layout |
| `apps/web/src/components/layout/AdminLayout.jsx` | Frontend Component | Layout wrapper for `/admin/*` routes | **Yes** | React Router Outlet | Core Layout |
| `apps/web/src/components/layout/PageHeader.jsx` | Frontend Component | Page header rendering title, subtitle, and action buttons | **Yes** | React | Core UI Component |
| `apps/web/src/pages/public/LandingPage.jsx` | Frontend Page | Public landing page directing users to Citizen, Authority, or Admin portals | **Yes** | React Router | Core Production |
| `apps/web/src/pages/public/LoginPage.jsx` | Frontend Page | Simulated login interface with quick-switch role presets (no backend auth) | **Yes** | React, React Router | Demo Scaffolding |
| `apps/web/src/pages/citizen/CitizenDashboardPage.jsx` | Frontend Page | Citizen home screen displaying active reports and quick actions | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/citizen/CitizenReportPage.jsx` | Frontend Page | 4-step civic issue filing wizard submitting real data to backend | **Yes** (Real API) | api.js (`createIncident`) | Core Production |
| `apps/web/src/pages/citizen/CitizenTrackPage.jsx` | Frontend Page | Citizen public tracking screen displaying timeline, SLA, and verified proof | **Yes** (Real API) | api.js (`getIncident`, `getIncidentTimeline`) | Core Production |
| `apps/web/src/pages/citizen/CitizenHistoryPage.jsx` | Frontend Page | Citizen submitted reports history list | **Yes** (Real API) | api.js (`getIncidents`) | Core Production |
| `apps/web/src/pages/citizen/CitizenFeedbackPage.jsx` | Frontend Page | Post-resolution citizen satisfaction feedback form | **Yes** (Local state only) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/citizen/CitizenSettingsPage.jsx` | Frontend Page | Citizen profile and notification settings screen | **Yes** (Static UI) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/authority/DashboardPage.jsx` | Frontend Page | Authority operational overview with live SLA stats and priority queue | **Yes** (Real API) | api.js (`getIncidents`) | Core Production |
| `apps/web/src/pages/authority/IncidentsPage.jsx` | Frontend Page | Searchable, filterable list of authority incidents | **Yes** (Real API) | api.js (`getIncidents`) | Core Production |
| `apps/web/src/pages/authority/AssignmentPage.jsx` | Frontend Page | Notice page explaining that officer/field assignment is not implemented | **Yes** (Static notice) | None | Explicit Boundary Note |
| `apps/web/src/pages/authority/VerificationPage.jsx` | Frontend Page | 4-stage resolution verification and closure interface | **Yes** (Real API) | api.js (`submitResolutionEvidence`, `verifyResolution`, `humanVerifyResolution`, `closeIncident`) | Core Production |
| `apps/web/src/pages/authority/LiveMapPage.jsx` | Frontend Page | Geographic incident distribution map (CSS percentage pins) | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/authority/SettingsPage.jsx` | Frontend Page | Authority agency settings and SLA threshold view | **Yes** (Static UI) | None | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminDashboardPage.jsx` | Frontend Page | Municipal executive dashboard with citywide KPIs | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminIncidentsPage.jsx` | Frontend Page | Citywide incident registry with multi-department filters | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminIncidentDetailPage.jsx` | Frontend Page | 7-tab deep inspection screen for incident `CT-1842` | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminSLAMonitoringPage.jsx` | Frontend Page | Cross-departmental SLA compliance monitoring | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminDepartmentPage.jsx` | Frontend Page | Department performance scorecards and workload metrics | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminGovernancePage.jsx` | Frontend Page | Civic accountability audit trail and escalation logs | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminAnalysisPage.jsx` | Frontend Page | Spatial clustering and recurrence analytics | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminMapPage.jsx` | Frontend Page | Municipal GIS map view with pin filters | **Yes** (Mock data) | mockData.js | Scaffolding / Mock |
| `apps/web/src/pages/admin/AdminSettingsPage.jsx` | Frontend Page | Systemwide governance configuration | **Yes** (Static UI) | None | Scaffolding / Mock |
| `bytexl/temp_seed.py` | Data / Seed | Master idempotent seeder importing Lucknow GIS zones, wards, authorities, assets | Manual Execution | SQLAlchemy, Shapely, GeoAlchemy2 | Seed Production |
| `bytexl/scripts/dev-setup.py` | Developer Tooling | One-shot environment configuration script copying `.env.example` | Manual Execution | Python standard library | Setup Utility |
| `bytexl/scripts/capture_*.js` | Visual Quality | Puppeteer scripts capturing high-res screenshots of frontend screens | CI / Test Only | Puppeteer | Testing Utility |
| `bytexl/scripts/verify_*.js` | Visual Quality | Visual verification scripts testing page rendering | CI / Test Only | Puppeteer | Testing Utility |
| `bytexl/scripts/check_runtime_errors.js` | Visual Quality | Puppeteer browser console error detector | CI / Test Only | Puppeteer | Testing Utility |
| `apps/api/test_workflow.py` | Debug Artifact | Manual verification script for Gate 3 orchestration | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/test_create.py` | Debug Artifact | Manual test script for incident creation | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/test_list.py` | Debug Artifact | Manual test script for incident listing | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/check_db.py` | Debug Artifact | Diagnostic script inspecting database records | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/verify_issue.py` | Debug Artifact | Diagnostic script for checking issue types | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/find_bad.py` | Debug Artifact | Diagnostic script finding constraint-violating records | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/add_constraint.py` | Debug Artifact | Script used to manually test constraint creation | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/fix.py` | Debug Artifact | Diagnostic database repair script | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/write_tests.py` | Debug Artifact | Code generation helper script | Developer Tool | Python standard library | Developer Scratch |
| `apps/api/test_workflow_query.py` | Debug Artifact | SQL query test script | Developer Tool | Python standard library | Developer Scratch |
| `test_db.py` | Root Debug Artifact | Root-level DB connection tester | Developer Tool | Python standard library | Developer Scratch |
| `test_point.py` | Root Debug Artifact | Root-level PostGIS point tester | Developer Tool | Python standard library | Developer Scratch |
| `test_workflow_match.py` | Root Debug Artifact | Root-level GIS workflow tester | Developer Tool | Python standard library | Developer Scratch |

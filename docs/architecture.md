# CivicTrace Architecture

## System Overview
CivicTrace is a civic issue intelligence and accountability platform. It processes incoming evidence (e.g., images, text, and coordinates), extracts structured data using AI perception, determines the responsible jurisdiction via GIS, fuses related reports, assigns priority, and tracks resolution accountability.

The system is built as a modular monolith. It exposes a FastAPI backend and a modern TypeScript frontend, backed by PostgreSQL with PostGIS for spatial operations.

## Component Diagram
```mermaid
graph TD
    Client[Web Frontend] --> API[FastAPI Gateway]
    
    subgraph Modular Monolith (FastAPI)
        API --> Routes
        Routes --> Services
        
        subgraph Domain Services
            AI[AI Perception - Gemini]
            GIS[GIS / Jurisdiction]
            Fusion[Incident Fusion]
            Priority[Priority Engine]
            Acct[Accountability & SLA]
            Verify[Resolution Verification]
        end
        
        Services --> Repo[Repositories]
    end
    
    Repo --> DB[(PostgreSQL + PostGIS)]
    AI -.-> GeminiProvider[Google Gemini API]
```

## Request Lifecycle (Evidence Capture to Incident)
1. **Evidence Capture:** Frontend submits evidence (image/text/location). Status becomes `PENDING`.
2. **AI Perception:** The `AIService` orchestrates the extraction. A `GeminiAIProvider` validates the output into an `AIAnalysisResult`. Validated data is persisted and status becomes `PROCESSED`. AI is explicitly forbidden from making accountability decisions.
3. **GIS Detection:** Coordinates are queried against GIS boundaries to find the responsible authority.
4. **Fusion:** System checks for recent, nearby incidents of the same category via deterministic weighting. If a match is found, evidence is appended. Otherwise, a new Incident is created.
5. **Priority Engine:** Computes priority score based on severity, safety risk, and persistence (time/count).
6. **Authority Assignment & SLA:** The incident is assigned to the jurisdiction with a computed due date and state (Pending/Due).
7. **Storage:** Data is persisted via Repositories to PostgreSQL.

## Data Flow
- **Evidence** is the atomic unit of user input.
- **Incidents** are the canonical records (aggregations of one or more Evidence items).
- **Authorities** define the SLA rules and manage jurisdiction states.
- Data flows uni-directionally from routes -> services -> repositories.

## Module Responsibilities
- **API Routes:** HTTP layer, routing, request/response validation.
- **Schemas/Contracts:** Pydantic models for data interchange and external system contracts.
- **Models:** SQLAlchemy ORM definitions mapping to database tables.
- **Repositories:** Data access layer isolating DB queries from business logic.
- **Services:** Core domain logic (Fusion, Priority, Accountability).
- **External Integrations:** Interface implementations for external AI or GIS services.

## Boundaries
- **Database Boundary:** All persistent state is in PostgreSQL. Spatial logic relies heavily on PostGIS.
- **AI Boundary:** AI models act strictly as "sensors". They convert unstructured data into structured schemas but never dictate SLAs or resolve incidents.
- **GIS Boundary:** Handles point-in-polygon queries, proximity searches, and spatial indexing.

## Core Strategies
- **Orchestration:** Monolithic synchronous processing for immediate APIs. Background tasks (via FastAPI BackgroundTasks) for AI processing and async fusion. No complex event buses.
- **Error Handling:** Standardized HTTP exception handlers. Service layer raises domain exceptions; API layer translates them to proper HTTP status codes.
- **Logging:** Structured JSON logging. All requests injected with a correlation ID to trace logs across the request lifecycle.
- **Configuration:** Environment variables managed via `pydantic-settings`.
- **Testing:** Unit tests for pure domain logic (Priority, Fusion). Integration tests for Repositories and GIS logic.
- **Deployment:** Dockerized containers orchestrated via Docker Compose for local development and standard container platforms for production.
- **Security Baseline:** JWT-based authentication. Input validation via Pydantic. Basic RBAC for authorities.

<div align="center">

# 🏛️ CivicTrace
### Intelligent Civic Issue Perception, Spatial Jurisdiction Routing & Accountability Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20PostGIS-336791?logo=postgresql&logoColor=white)](https://postgis.net/)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-Multimodal%20Perception-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Azure AI](https://img.shields.io/badge/Microsoft%20Azure-Vision%20%7C%20Speech%20%7C%20Language-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<p align="center">
  <b>CivicTrace</b> connects on-the-ground citizen complaints with responsible municipal authorities.<br/>
  By combining multimodal AI perception, PostGIS point-in-polygon spatial containment, automated SLA state machines, and evidence-verified resolution audits, CivicTrace delivers complete transparency and accountability in civic governance.
</p>

[Key Principles](#-architectural-principles) •
[Portals & Features](#-portals--features) •
[Architecture](#-system-architecture) •
[Tech Stack](#-tech-stack) •
[Getting Started](#-getting-started) •
[Testing](#-testing--quality-assurance)

---

</div>

## 💡 Architectural Principles

CivicTrace is built on four non-negotiable engineering principles:

1. 👁️ **AI is for Perception Only**: Multimodal AI (Google Gemini & Azure AI) extracts issue categories, severity levels, and hazard descriptions from citizen photos, audio recordings, and text notes. AI **never** makes unexplainable administrative or closure decisions.
2. 🗺️ **GIS Determines Jurisdiction**: PostGIS `ST_Contains` point-in-polygon spatial queries automatically map complaint coordinates to exact administrative boundaries and assign the responsible authority (e.g., Municipal Corporation, Water Board, PWD, Electricity Board).
3. ⏱️ **Deterministic SLA Engine**: Mathematical SLA rules monitor deadlines per department and issue type. A background poller automatically flags at-risk complaints and records immutable escalation events on breaches.
4. 📸 **Evidence-Backed Verification**: Field officers must upload physical photo proof of completed work. Before-and-after evidence is evaluated before an issue can transition to `CLOSED`.

---

## 🚀 Portals & Features

### 👤 Citizen Experience (`/citizen`)
* **4-Step Issue Submission**: Upload evidence photos, record voice notes with automated Hindi/English Speech-to-Text transcription, pick categories, and pin location on a map.
* **Live Incident Tracking**: Real-time progress timeline, assigned authority details, SLA countdown timers, and public audit history.
* **Resolution Proof**: Inspect verified before-and-after photo evidence once work is finished.

### 🏢 Authority Command Hub (`/authority`)
* **Operational Dashboard**: Live SLA metrics (open, at risk, breached, resolved) and priority incident queues filtered by department jurisdiction.
* **Interactive Live Map**: Geographic distribution and spatial clustering across municipal operational zones.
* **4-Stage Verification Hub**: Submit work proof, run resolution verification checks, and close complaints with officer authentication.

### 📊 Municipal Executive & Admin Portal (`/admin`)
* **Citywide Governance Dashboard**: Unified executive KPIs aggregated across all municipal departments.
* **Cross-Agency SLA Compliance**: Real-time monitoring of department response times, breach rates, and escalation logs.
* **Department Scorecards**: Workload distribution, resolution performance, and response rankings.
* **Spatial Analytics & Hotspots**: Spatial proximity clustering (`ST_DistanceSphere`) to identify chronic infrastructure failure patterns.

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend Web App (React 18 + Vite)"]
        CP["Citizen Portal\n(Photo / Audio / Geo-Coords)"]
        AP["Authority Portal\n(Resolution Verification)"]
        AD["Admin Portal\n(Governance & Spatial KPIs)"]
    end

    subgraph Backend ["Backend API (FastAPI + Python 3.11)"]
        API["FastAPI Routes & Auth (JWT/RBAC)"]
        
        subgraph Perception ["Multimodal AI Perception Layer"]
            GEM["Google Gemini 1.5 / 2.0"]
            AZ_V["Azure Computer Vision"]
            AZ_S["Azure Speech STT (Web Audio WAV)"]
            AZ_L["Azure Language & Translation"]
        end
        
        subgraph CoreServices ["Domain Service Layer"]
            GIS["GIS Service (PostGIS ST_Contains)"]
            FUS["Incident Fusion (Deduplication)"]
            SLA["SLA Engine & Poller (Async Loop)"]
            VER["Verification Engine (Proof Auditing)"]
        end
    end

    subgraph Storage ["Database & Storage Layer"]
        PG[("PostgreSQL 16 + PostGIS\n(Spatial Wards, Boundaries, SLAs, Users)")]
        OBJ[("Object Storage\n(Evidence Media Assets)")]
    end

    CP -->|"Submit Issue"| API
    AP -->|"Submit Proof & Close"| API
    AD -->|"Audit & Analytics"| API
    
    API --> Perception
    API --> CoreServices
    
    CoreServices --> PG
    API --> OBJ
```

---

## 🛠️ Tech Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) | Async REST API with automatic OpenAPI Swagger docs and dependency injection. |
| **Database & GIS** | [PostgreSQL 16](https://www.postgresql.org/) + [PostGIS 3.4](https://postgis.net/) | Spatial indexing, geometry storage (`POINT`, `MULTIPOLYGON`), and spatial containment queries. |
| **ORM & Migrations** | [SQLAlchemy 2.0 (Async)](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) | Async relational data access with type safety and schema versioning. |
| **AI Perception** | [Google Gemini](https://ai.google.dev/) + [Azure AI](https://azure.microsoft.com/) | Multimodal image analysis, speech-to-text audio transcription, and language translation. |
| **Frontend UI** | [React 18](https://react.dev/) + [Vite](https://vitejs.dev/) | High-performance Single Page Application with custom semantic design tokens. |
| **Routing & Auth** | [React Router v6](https://reactrouter.com/) + JWT | Multi-portal routing with role-based access control (`citizen`, `authority_officer`, `admin`). |
| **Testing** | [Pytest](https://docs.pytest.org/) (28 test suites) | Automated unit, integration, and full lifecycle end-to-end testing. |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- **PostgreSQL 16** with **PostGIS** extension enabled

---

### 1. Database Setup

Ensure PostgreSQL is running and PostGIS is enabled on your database:

```sql
CREATE DATABASE civictrace;
\c civictrace
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

---

### 2. Backend Setup (FastAPI)

```bash
# Navigate to API directory
cd apps/api

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../../.env.example .env
# Update .env with your PostgreSQL credentials and API keys

# Apply database migrations
alembic upgrade head

# Seed demo municipal dataset (Lucknow zones, wards, authorities, sample incidents)
python ../../scripts/seed_lucknow_data.py

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at:
- **API Base**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Docs**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

### 3. Frontend Setup (React + Vite)

In a new terminal window:

```bash
# Navigate to web directory
cd apps/web

# Install npm dependencies
npm install

# Start the Vite development server
npm run dev
```

Visit **`http://localhost:5173`** in your browser to explore the portals.

---

## ⚙️ Environment Configuration

Create a `.env` file in the root or `apps/api/` folder:

```env
# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1
SECRET_KEY=your-jwt-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# PostgreSQL + PostGIS Database URL
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/civictrace

# AI Perception Providers
GEMINI_API_KEY=your-google-gemini-api-key
AZURE_VISION_KEY=your-azure-vision-key
AZURE_VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=centralindia
AZURE_LANGUAGE_KEY=your-azure-language-key
AZURE_LANGUAGE_ENDPOINT=https://your-language-resource.cognitiveservices.azure.com/

# Storage
STORAGE_BACKEND=local
```

---

## 🧪 Testing & Quality Assurance

CivicTrace features 28 automated test suites covering all domain logic, GIS math, SLA state transitions, and security checks:

```bash
cd apps/api

# Run full test suite
pytest

# Run with test coverage report
pytest --cov=app --cov-report=term-missing

# Run specific functional suites
pytest tests/test_gis.py -v                  # PostGIS point-in-polygon containment
pytest tests/test_sla.py -v                  # SLA calculation & state progression
pytest tests/test_auth.py -v                 # JWT & RBAC access control
pytest tests/test_verification.py -v         # Evidence-backed resolution evaluation
pytest tests/test_fusion.py -v               # Duplicate incident fusion & clustering
pytest tests/test_gate4_hardening.py -v      # Database invariant integrity
pytest tests/test_e2e_pipeline.py -v         # Complete report-to-closure lifecycle
```

---

## 📁 Repository Structure

```
CivicTrace/
├── apps/
│   ├── api/                          # FastAPI Backend Application
│   │   ├── alembic/                  # Database schema migrations
│   │   ├── app/
│   │   │   ├── api/                  # Route handlers (incidents, auth, ai, system, health)
│   │   │   ├── core/                 # Config, async database, logging, errors, security
│   │   │   ├── models/               # SQLAlchemy models (Incident, Location, SLA, User, etc.)
│   │   │   ├── schemas/              # Pydantic v2 validation contracts
│   │   │   ├── repositories/         # Database data access layer
│   │   │   ├── services/             # Domain logic (GIS, SLA, Verification, Fusion, AI)
│   │   │   └── main.py               # Application factory & SLA background poller
│   │   └── tests/                    # 28 Pytest automated test suites
│   └── web/                          # React 18 + Vite Frontend Application
│       └── src/
│           ├── components/           # Shared UI components & portal layouts
│           ├── pages/                # Citizen, Authority, Admin, and Public portals
│           ├── routes/               # Route definitions with role scoping
│           ├── services/             # REST API client (`api.js`)
│           └── styles/               # Global styles & design tokens
├── docs/                             # Architecture specifications & contracts
├── scripts/                          # Seeder scripts (`seed_lucknow_data.py`) & tooling
└── README.md                         # Project documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

<div align="center">
  <sub>Built for Transparent, Accountable, and Responsive Civic Governance.</sub>
</div>

# CivicTrace

CivicTrace is a civic issue intelligence and accountability platform. It connects on-the-ground evidence with responsible authorities using AI perception and GIS determination.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2
- Python 3.11+ (for local development outside Docker)
- Node.js 20+ (for the frontend)

## Quick Start (Docker — Recommended)

```bash
# 1. Clone the repository
git clone <repo-url>
cd civictrace

# 2. Copy the environment template
cp .env.example .env
# Edit .env if you need to override any defaults (see Configuration section below)

# 3. Start the full development stack
docker compose up --build

# 4. Verify the API is healthy
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"civictrace-api"}

# 5. Apply database migrations (separate terminal, or after containers are up)
docker compose exec api alembic upgrade head
```

The stack starts:
| Service   | URL                        |
|-----------|----------------------------|
| API       | http://localhost:8000      |
| API Docs  | http://localhost:8000/docs |
| DB        | localhost:5432             |

## Local Development (Without Docker)

```bash
cd apps/api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp ../../.env.example .env

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
cd apps/api

# Run the full test suite
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_health.py -v
```

## Configuration

All configuration is driven by environment variables. See [.env.example](.env.example) for the full list.

| Variable                | Default                                      | Description                              |
|-------------------------|----------------------------------------------|------------------------------------------|
| `ENVIRONMENT`           | `development`                                | `development`, `staging`, or `production`|
| `LOG_LEVEL`             | `INFO`                                       | Logging verbosity                        |
| `DATABASE_URL`          | `postgresql+asyncpg://...`                   | Full async DSN for PostgreSQL/PostGIS    |
| `ALLOWED_ORIGINS`       | `http://localhost:3000`                      | Comma-separated CORS origins             |
| `SECRET_KEY`            | *(required in production)*                   | JWT signing secret                       |
| `GEMINI_API_KEY`        | *(empty)*                                    | Google Gemini API key for AI Perception  |

## Project Structure

```
civictrace/
├── apps/
│   ├── api/                  # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/          # Route handlers and dependencies
│   │   │   ├── core/         # Config, logging, error handling, security
│   │   │   ├── models/       # SQLAlchemy ORM models
│   │   │   ├── schemas/      # Pydantic request/response schemas
│   │   │   ├── repositories/ # Data access layer
│   │   │   ├── services/     # Domain service layer
│   │   │   └── main.py       # Application factory
│   │   ├── alembic/          # Database migrations
│   │   ├── tests/            # Test suite
│   │   └── requirements.txt
│   └── web/                  # TypeScript frontend (upcoming)
├── packages/shared/          # Shared types and constants
├── data/                     # Seed data and GIS layers
├── docs/                     # Architecture, ADRs, and contracts
├── infra/                    # Docker and deployment configs
└── scripts/                  # Utility scripts
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

Key principles:
- **AI is for perception only** — not accountability decisions
- **GIS determines jurisdiction** — point-in-polygon authority assignment
- **Deterministic fusion** — explainable incident grouping
- **Modular monolith** — clean service boundaries, simple deployment

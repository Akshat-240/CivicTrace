# =============================================================================
# CivicTrace API — Development Dockerfile
# =============================================================================
# Multi-stage build is overkill for MVP development. This Dockerfile is
# optimised for fast rebuilds via layer caching.
# A production-grade multi-stage image will be added before staging.
# =============================================================================

FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered stdout for clean container logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system-level dependencies needed by asyncpg and psycopg compilation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies as a separate layer so they are cached
# between code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY . .

EXPOSE 8000

# Default command — overridden in docker-compose.yml with --reload.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

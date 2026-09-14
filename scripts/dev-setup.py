#!/usr/bin/env python3
"""
dev-setup.py — One-shot local development setup script.

Run from the repository root:
    python scripts/dev-setup.py

What it does:
1. Copies .env.example to .env (if .env doesn't exist)
2. Prints next steps for Docker and local development
"""

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ENV_EXAMPLE = REPO_ROOT / ".env.example"
ENV_FILE = REPO_ROOT / ".env"


def main():
    # Copy .env.example -> .env
    if ENV_FILE.exists():
        print(f"[skip] .env already exists at {ENV_FILE}")
    else:
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        print(f"[ok]   Created {ENV_FILE} from .env.example")
        print("       Edit .env and set a strong SECRET_KEY before deploying.\n")

    print("\n=== CivicTrace Dev Setup ===\n")
    print("Option A — Docker (recommended):")
    print("  docker compose up --build")
    print("  docker compose exec api alembic upgrade head")
    print("  curl http://localhost:8000/health\n")
    print("Option B — Local Python:")
    print("  cd apps/api")
    print("  python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  alembic upgrade head")
    print("  uvicorn app.main:app --reload\n")
    print("Run tests:")
    print("  cd apps/api && pytest\n")


if __name__ == "__main__":
    main()

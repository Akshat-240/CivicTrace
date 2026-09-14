"""
FastAPI shared dependencies.

All shared dependencies that route handlers consume via Depends() live here.
Keeping them in one place makes test overriding trivial:

    app.dependency_overrides[get_db] = my_test_session_factory

Current dependencies:
- get_db:       Yields a scoped async SQLAlchemy session.
- get_settings: Returns the cached settings instance.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db

# Typed aliases — use these in route function signatures for cleaner code.
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

"""
Tests for database connectivity and session lifecycle.

These tests run against a real PostgreSQL/PostGIS database.
They are skipped automatically if the test database is unreachable.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.mark.asyncio
async def test_db_session_executes_query(db_session):
    """A session yielded by get_db() must be able to run a simple query."""
    result = await db_session.execute(text("SELECT 1 AS val"))
    row = result.fetchone()
    assert row is not None
    assert row.val == 1


@pytest.mark.asyncio
async def test_db_session_rollback_on_error(db_session):
    """
    Verify that exceptions inside a session do not corrupt the connection.
    The session should still be usable after a rollback.
    """
    try:
        # Intentionally run an invalid query.
        await db_session.execute(text("SELECT * FROM nonexistent_table_xyz"))
    except Exception:
        await db_session.rollback()

    # After rollback, the session must still be operational.
    result = await db_session.execute(text("SELECT 1 AS val"))
    row = result.fetchone()
    assert row.val == 1


@pytest.mark.asyncio
async def test_postgis_extension_available(db_session):
    """
    Verify that PostGIS is installed on the test database.

    This test fails deliberately if PostGIS is missing, which surfaces
    the issue during CI rather than at runtime.
    """
    result = await db_session.execute(
        text("SELECT PostGIS_Version()")
    )
    row = result.fetchone()
    assert row is not None, "PostGIS extension is not installed."
    # PostGIS version string is non-empty.
    assert row[0]

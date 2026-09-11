"""
Initial migration: enable PostGIS extension.

This is the first migration in CivicTrace. It enables the PostGIS
extension on the database so that all subsequent models can use
geometry columns.

Revision ID: 0001
Revises: (none)
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001_enable_postgis"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS. This is idempotent — safe to run multiple times.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")


def downgrade() -> None:
    # NOTE: Dropping PostGIS will fail if geometry columns exist.
    # Run downgrade only on a clean database or after dropping all geometry columns.
    op.execute("DROP EXTENSION IF EXISTS postgis_topology")
    op.execute("DROP EXTENSION IF EXISTS postgis")

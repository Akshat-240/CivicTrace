"""Add jurisdiction-authority invariant constraint

Revision ID: 0003_jur_auth_invariant
Revises: 43389400dc2b
Create Date: 2026-09-14 00:05:00.000000+00:00

Enforces the CivicTrace domain invariant:
  IF jurisdiction_id IS NULL THEN authority_id MUST be NULL.
  IF jurisdiction_id IS NOT NULL THEN authority_id MAY be set.

This prevents orphan authority assignments that bypass the GIS workflow.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003_jur_auth_invariant'
down_revision: Union[str, None] = '43389400dc2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the domain invariant constraint.
    # Allows:
    #   (jurisdiction_id IS NULL AND authority_id IS NULL)  -- no GIS match yet
    #   (jurisdiction_id IS NOT NULL)                       -- GIS matched, authority optional
    # Rejects:
    #   (jurisdiction_id IS NULL AND authority_id IS NOT NULL)  -- orphan assignment
    #
    # Uses a DO block so this migration is safe whether the constraint was
    # previously added manually (via ALTER TABLE) or not (clean install).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_incidents_jurisdiction_authority_invariant'
                  AND conrelid = 'incidents'::regclass
            ) THEN
                ALTER TABLE incidents
                    ADD CONSTRAINT ck_incidents_jurisdiction_authority_invariant
                    CHECK (
                        (jurisdiction_id IS NULL AND authority_id IS NULL)
                        OR (jurisdiction_id IS NOT NULL)
                    );
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        'ck_incidents_jurisdiction_authority_invariant',
        'incidents',
        type_='check',
    )

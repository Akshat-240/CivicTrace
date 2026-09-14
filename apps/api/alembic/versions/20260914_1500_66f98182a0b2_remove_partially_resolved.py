"""Remove PARTIALLY_RESOLVED and update verification_records constraint

Revision ID: 66f98182a0b2
Revises: 55e82b7190f1
Create Date: 2026-09-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66f98182a0b2'
down_revision: Union[str, None] = '55e82b7190f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old check constraint first so data update doesn't violate it
    op.execute("ALTER TABLE verification_records DROP CONSTRAINT IF EXISTS ck_verification_result")

    # 2. Migrate existing verification_records data
    op.execute("UPDATE verification_records SET result = 'not_resolved' WHERE result IN ('unresolved', 'partially_resolved')")
    op.execute("UPDATE verification_records SET result = 'no_evidence' WHERE result = 'insufficient_evidence'")

    # 3. Create updated check constraint with target 4 states
    op.create_check_constraint(
        "ck_verification_result",
        "verification_records",
        "result IS NULL OR result IN ('fully_resolved', 'not_resolved', 'no_evidence', 'human_review')"
    )


def downgrade() -> None:
    # 1. Drop updated check constraint first
    op.execute("ALTER TABLE verification_records DROP CONSTRAINT IF EXISTS ck_verification_result")

    # 2. Map values back for downgrade compatibility
    op.execute("UPDATE verification_records SET result = 'unresolved' WHERE result IN ('not_resolved', 'human_review')")
    op.execute("UPDATE verification_records SET result = 'insufficient_evidence' WHERE result = 'no_evidence'")

    # 3. Re-create old check constraint
    op.create_check_constraint(
        "ck_verification_result",
        "verification_records",
        "result IS NULL OR result IN ('fully_resolved', 'partially_resolved', 'unresolved', 'insufficient_evidence')"
    )


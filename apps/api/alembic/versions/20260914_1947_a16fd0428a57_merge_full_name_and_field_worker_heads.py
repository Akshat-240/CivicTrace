"""merge_full_name_and_field_worker_heads

Revision ID: a16fd0428a57
Revises: e825aa24a27f, db714d235900
Create Date: 2026-09-14 19:47:06.004291+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a16fd0428a57'
down_revision: Union[str, None] = ('e825aa24a27f', 'db714d235900')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

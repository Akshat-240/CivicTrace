'''Add User role authority check constraint

Revision ID: 44d65eee453a
Revises: f422f8521f95
Create Date: 2026-09-13 14:40:48.337035

'''
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44d65eee453a'
down_revision: Union[str, None] = 'f422f8521f95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        'users_role_authority_check',
        'users',
        '''
        (role IN ('CITIZEN', 'ADMIN') AND authority_id IS NULL)
        OR (role = 'AUTHORITY' AND authority_id IS NOT NULL)
        '''
    )


def downgrade() -> None:
    op.drop_constraint('users_role_authority_check', 'users', type_='check')




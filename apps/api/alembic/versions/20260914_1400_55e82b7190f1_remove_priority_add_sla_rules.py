"""Remove priority table and add sla_rules table

Revision ID: 55e82b7190f1
Revises: 0003_jur_auth_invariant, 44d65eee453a
Create Date: 2026-09-14 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55e82b7190f1'
down_revision: Union[str, Sequence[str], None] = ('0003_jur_auth_invariant', '44d65eee453a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sla_rules table
    op.create_table(
        'sla_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('authority_id', sa.Uuid(), nullable=False),
        sa.Column('issue_type', sa.String(length=50), nullable=False),
        sa.Column('resolution_hours', sa.Integer(), nullable=False),
        sa.Column('escalation_grace_hours', sa.Integer(), nullable=False, server_default='72'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['authority_id'], ['authorities.id'], name=op.f('sla_rules_authority_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('sla_rules_pkey')),
        sa.UniqueConstraint('authority_id', 'issue_type', name='uq_sla_rules_authority_issue_type'),
        sa.CheckConstraint('resolution_hours > 0', name='ck_sla_rules_resolution_hours_positive'),
        sa.CheckConstraint('escalation_grace_hours >= 0', name='ck_sla_rules_escalation_grace_hours_non_negative')
    )
    op.create_index(op.f('ix_sla_rules_authority_id'), 'sla_rules', ['authority_id'], unique=False)
    op.create_index(op.f('ix_sla_rules_issue_type'), 'sla_rules', ['issue_type'], unique=False)

    # 2. Drop legacy priorities table safely
    op.execute("DROP TABLE IF EXISTS priorities CASCADE;")


def downgrade() -> None:
    op.drop_index(op.f('ix_sla_rules_issue_type'), table_name='sla_rules')
    op.drop_index(op.f('ix_sla_rules_authority_id'), table_name='sla_rules')
    op.drop_table('sla_rules')

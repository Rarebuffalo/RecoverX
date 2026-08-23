"""004_enhance_recovery_actions_and_opportunities

Revision ID: 004_enhance_actions_opps
Revises: 003_add_agent_runs_table
Create Date: 2026-08-21 17:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_enhance_actions_opps'
down_revision: Union[str, None] = '003_add_agent_runs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recovery_actions', sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('recovery_actions', sa.Column('payment_link_url', sa.String(length=500), nullable=True))
    op.add_column('recovery_actions', sa.Column('error_category', sa.String(length=50), nullable=True))
    op.add_column('recovery_actions', sa.Column('error_message', sa.String(length=500), nullable=True))
    op.add_column('recovery_actions', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_recovery_actions_provider_id', 'recovery_actions', ['provider_action_id'])


def downgrade() -> None:
    op.drop_index('idx_recovery_actions_provider_id', table_name='recovery_actions')
    op.drop_column('recovery_actions', 'completed_at')
    op.drop_column('recovery_actions', 'error_message')
    op.drop_column('recovery_actions', 'error_category')
    op.drop_column('recovery_actions', 'payment_link_url')
    op.drop_column('recovery_actions', 'attempt_number')

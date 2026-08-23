"""003_add_agent_runs_table

Revision ID: 003_add_agent_runs_table
Revises: 002_add_policy_version
Create Date: 2026-08-21 17:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '003_add_agent_runs_table'
down_revision: Union[str, None] = '002_add_policy_version'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('opportunity_id', sa.Uuid(as_uuid=True), sa.ForeignKey('recovery_opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='recovery-diagnostic-v1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUCCESS'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_agent_runs_opp', 'agent_runs', ['opportunity_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_agent_runs_opp', table_name='agent_runs')
    op.drop_table('agent_runs')

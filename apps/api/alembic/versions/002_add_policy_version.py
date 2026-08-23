"""002_add_policy_version

Revision ID: 002_add_policy_version
Revises: 001_initial_schema
Create Date: 2026-08-21 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_policy_version'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'recovery_decisions',
        sa.Column('policy_version', sa.String(length=20), nullable=True, server_default='v1')
    )


def downgrade() -> None:
    op.drop_column('recovery_decisions', 'policy_version')

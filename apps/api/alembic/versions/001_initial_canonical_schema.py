"""001_initial_canonical_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-21 15:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Merchants Table
    op.create_table(
        'merchants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('razorpay_account_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_merchants_email'),
    )
    op.create_index('ix_merchants_email', 'merchants', ['email'], unique=True)

    # 2. Customers Table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('lifetime_value_inr', sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('total_orders', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('successful_orders', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id', 'email', name='uq_merchant_customer_email'),
    )
    op.create_index('idx_customers_merchant_email', 'customers', ['merchant_id', 'email'])
    op.create_index('idx_customers_merchant_phone', 'customers', ['merchant_id', 'phone'])
    op.create_index('ix_customers_merchant_id', 'customers', ['merchant_id'])

    # 3. Merchant Policies Table
    op.create_table(
        'merchant_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('auto_recovery_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('max_retry_attempts', sa.Integer(), nullable=False, server_default=sa.text('2')),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('max_auto_recovery_amount_inr', sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text('10000.00')),
        sa.Column('max_customer_contact_per_day', sa.Integer(), nullable=False, server_default=sa.text('2')),
        sa.Column('escalation_after_failed_attempts', sa.Integer(), nullable=False, server_default=sa.text('2')),
        sa.Column('allowed_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id', name='uq_merchant_policies_merchant_id'),
    )
    op.create_index('idx_merchant_policies_merchant', 'merchant_policies', ['merchant_id'], unique=True)

    # 4. Orders Table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_order_id', sa.String(length=100), nullable=True),
        sa.Column('amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_orders_merchant_status', 'orders', ['merchant_id', 'status'])
    op.create_index('idx_orders_provider_order_id', 'orders', ['provider_order_id'])
    op.create_index('idx_orders_customer_created', 'orders', ['customer_id', 'created_at'])
    op.create_index('ix_orders_customer_id', 'orders', ['customer_id'])
    op.create_index('ix_orders_merchant_id', 'orders', ['merchant_id'])

    # 5. Payment Attempts Table
    op.create_table(
        'payment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_payment_id', sa.String(length=100), nullable=True),
        sa.Column('method', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('failure_code', sa.String(length=100), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_payment_id', name='uq_payment_attempts_provider_id'),
    )
    op.create_index('idx_payment_attempts_merchant_status', 'payment_attempts', ['merchant_id', 'status'])
    op.create_index('idx_payment_attempts_order_created', 'payment_attempts', ['order_id', 'created_at'])
    op.create_index('idx_payment_attempts_provider_id', 'payment_attempts', ['provider_payment_id'])
    op.create_index('ix_payment_attempts_merchant_id', 'payment_attempts', ['merchant_id'])
    op.create_index('ix_payment_attempts_order_id', 'payment_attempts', ['order_id'])

    # 6. Recovery Opportunities Table
    op.create_table(
        'recovery_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DETECTED'),
        sa.Column('revenue_at_risk_inr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('recovered_amount_inr', sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('recovery_score', sa.Integer(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_recovery_opportunities_order_id'),
    )
    op.create_index('idx_recovery_opps_merchant_status', 'recovery_opportunities', ['merchant_id', 'status'])
    op.create_index('idx_recovery_opps_created', 'recovery_opportunities', ['created_at'])
    op.create_index('idx_recovery_opps_next_retry', 'recovery_opportunities', ['next_retry_at'])
    op.create_index('ix_recovery_opportunities_merchant_id', 'recovery_opportunities', ['merchant_id'])
    op.create_index('ix_recovery_opportunities_order_id', 'recovery_opportunities', ['order_id'])

    # 7. Recovery Decisions Table
    op.create_table(
        'recovery_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_model', sa.String(length=100), nullable=True),
        sa.Column('diagnosis_category', sa.String(length=100), nullable=False),
        sa.Column('recommended_action', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('reasoning_summary', sa.Text(), nullable=False),
        sa.Column('fallback_action', sa.String(length=100), nullable=True),
        sa.Column('signals', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['opportunity_id'], ['recovery_opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_recovery_decisions_opp', 'recovery_decisions', ['opportunity_id', 'created_at'])
    op.create_index('ix_recovery_decisions_opportunity_id', 'recovery_decisions', ['opportunity_id'])

    # 8. Recovery Actions Table
    op.create_table(
        'recovery_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=150), nullable=False),
        sa.Column('policy_approved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('policy_rejection_reasons', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('provider_action_id', sa.String(length=150), nullable=True),
        sa.Column('action_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['decision_id'], ['recovery_decisions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['recovery_opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_recovery_actions_idempotency'),
    )
    op.create_index('idx_recovery_actions_opp', 'recovery_actions', ['opportunity_id', 'created_at'])
    op.create_index('idx_recovery_actions_idempotency', 'recovery_actions', ['idempotency_key'], unique=True)
    op.create_index('idx_recovery_actions_status', 'recovery_actions', ['execution_status'])
    op.create_index('ix_recovery_actions_opportunity_id', 'recovery_actions', ['opportunity_id'])

    # 9. Processed Webhooks Table
    op.create_table(
        'processed_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='razorpay'),
        sa.Column('event_id', sa.String(length=150), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'event_id', name='uq_provider_event_id'),
    )
    op.create_index('idx_processed_webhooks_lookup', 'processed_webhooks', ['provider', 'event_id'])

    # 10. Audit Events Table
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=False, server_default='SYSTEM'),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_summary', sa.Text(), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('previous_event_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['recovery_opportunities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_events_opp_created', 'audit_events', ['opportunity_id', 'created_at'])
    op.create_index('idx_audit_events_merchant_created', 'audit_events', ['merchant_id', 'created_at'])
    op.create_index('ix_audit_events_merchant_id', 'audit_events', ['merchant_id'])
    op.create_index('ix_audit_events_opportunity_id', 'audit_events', ['opportunity_id'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('processed_webhooks')
    op.drop_table('recovery_actions')
    op.drop_table('recovery_decisions')
    op.drop_table('recovery_opportunities')
    op.drop_table('payment_attempts')
    op.drop_table('orders')
    op.drop_table('merchant_policies')
    op.drop_table('customers')
    op.drop_table('merchants')

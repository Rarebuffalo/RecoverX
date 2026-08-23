import uuid
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    MerchantPolicy,
    RecoveryAction,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    ActionExecutionStatus,
    RecoveryActionType,
)
from app.services.executor.action_executor_service import ActionExecutorService
from app.services.executor.adapters.mock_adapter import LocalDeterministicMockAdapter


@pytest.mark.asyncio
async def test_action_execution_lifecycle_and_idempotency(db_session: AsyncSession):
    merchant = Merchant(name="Exec Store", email="exec_test@example.com", razorpay_account_id="acc_exec_01")
    db_session.add(merchant)
    await db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        email="exec_cust@example.com",
        lifetime_value_inr=Decimal("15000.00"),
        total_orders=3,
        successful_orders=3,
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_exec_01",
        amount_inr=Decimal("5000.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("5000.00"),
        attempt_count=0,
    )
    db_session.add(opp)
    await db_session.commit()

    # 1. Queue Action
    action = await ActionExecutorService.create_and_queue_action(
        db_session, opportunity_id=opp.id
    )
    assert action.execution_status == ActionExecutionStatus.QUEUED
    assert action.idempotency_key == f"recovery:{opp.id}:attempt:1"

    # 2. Duplicate Queue Call returns existing action
    dup_action = await ActionExecutorService.create_and_queue_action(
        db_session, opportunity_id=opp.id
    )
    assert dup_action.id == action.id

    # 3. Execute Action
    mock_adapter = LocalDeterministicMockAdapter()
    exec_action, result = await ActionExecutorService.execute_action(
        db_session, action_id=action.id, adapter_override=mock_adapter
    )
    assert exec_action.execution_status == ActionExecutionStatus.SUCCEEDED
    assert exec_action.payment_link_url.startswith("https://rzp.io/i/mock_")
    assert exec_action.provider_action_id.startswith("plink_mock_")

    # Verify opportunity transitioned to INTERVENED
    await db_session.refresh(opp)
    assert opp.status == OpportunityStatus.INTERVENED
    assert opp.attempt_count == 1

    # 4. Re-execution of SUCCEEDED action is idempotent
    re_action, re_result = await ActionExecutorService.execute_action(
        db_session, action_id=action.id, adapter_override=mock_adapter
    )
    assert re_action.execution_status == ActionExecutionStatus.SUCCEEDED
    assert re_result is None


@pytest.mark.asyncio
async def test_pre_execution_check_paid_order_cancels_action(db_session: AsyncSession):
    merchant = Merchant(name="Paid Order Store", email="paid_exec@example.com", razorpay_account_id="acc_exec_02")
    db_session.add(merchant)
    await db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        email="paid_cust@example.com",
        lifetime_value_inr=Decimal("3000.00"),
        total_orders=1,
        successful_orders=1,
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_exec_paid_01",
        amount_inr=Decimal("3000.00"),
        status=OrderStatus.PAID,  # Already PAID!
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("3000.00"),
    )
    db_session.add(opp)
    await db_session.commit()

    action = await ActionExecutorService.create_and_queue_action(
        db_session, opportunity_id=opp.id
    )

    exec_action, result = await ActionExecutorService.execute_action(
        db_session, action_id=action.id
    )
    assert exec_action.execution_status == ActionExecutionStatus.CANCELLED
    assert exec_action.error_category == "ORDER_ALREADY_PAID"
    assert result is None

import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    RecoveryAction,
    MerchantPolicy,
    ProcessedWebhook,
    AuditEvent,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    RecoveryActionType,
    ActionExecutionStatus,
    ActorType,
)


@pytest.mark.asyncio
async def test_merchant_and_customer_creation(db_session: AsyncSession):
    # 1. Create Merchant
    merchant = Merchant(
        name="Test Store",
        email="owner@teststore.com",
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)
    assert merchant.id is not None
    assert merchant.is_active is True

    # 2. Create Customer
    customer = Customer(
        merchant_id=merchant.id,
        name="John Doe",
        email="john@example.com",
        phone="+919876543210",
        lifetime_value_inr=Decimal("5000.00"),
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    assert customer.id is not None
    assert customer.merchant_id == merchant.id


@pytest.mark.asyncio
async def test_customer_merchant_unique_constraint(db_session: AsyncSession):
    merchant = Merchant(name="Unique Store", email="unique@store.com")
    db_session.add(merchant)
    await db_session.commit()

    cust1 = Customer(merchant_id=merchant.id, email="duplicate@example.com")
    db_session.add(cust1)
    await db_session.commit()

    # Attempting to add duplicate email under SAME merchant must fail
    cust2 = Customer(merchant_id=merchant.id, email="duplicate@example.com")
    db_session.add(cust2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_order_and_payment_attempts(db_session: AsyncSession):
    merchant = Merchant(name="Orders Store", email="orders@store.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, email="buyer@example.com")
    db_session.add(customer)
    await db_session.commit()

    # Create Order
    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_test_123",
        amount_inr=Decimal("4999.00"),
        status=OrderStatus.CREATED,
    )
    db_session.add(order)
    await db_session.commit()

    # Create Payment Attempt 1: Failed
    attempt1 = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_test_001",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("4999.00"),
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
    )
    db_session.add(attempt1)
    await db_session.commit()

    # Create Payment Attempt 2: Captured (Recovered)
    attempt2 = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_test_002",
        method="upi",
        status=PaymentAttemptStatus.CAPTURED,
        amount_inr=Decimal("4999.00"),
    )
    db_session.add(attempt2)
    await db_session.commit()

    # Verify duplicate provider_payment_id fails
    attempt_duplicate = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_test_001",  # duplicate
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("4999.00"),
    )
    db_session.add(attempt_duplicate)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_recovery_action_idempotency_key_uniqueness(db_session: AsyncSession):
    merchant = Merchant(name="Action Store", email="action@store.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, email="action_buyer@example.com")
    db_session.add(customer)
    await db_session.commit()

    order = Order(merchant_id=merchant.id, customer_id=customer.id, amount_inr=Decimal("1200.00"))
    db_session.add(order)
    await db_session.commit()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("1200.00"),
    )
    db_session.add(opp)
    await db_session.commit()

    # Action 1
    action1 = RecoveryAction(
        opportunity_id=opp.id,
        action_type=RecoveryActionType.CREATE_PAYMENT_LINK,
        idempotency_key="idem_key_unique_101",
        policy_approved=True,
        execution_status=ActionExecutionStatus.SUCCESS,
    )
    db_session.add(action1)
    await db_session.commit()

    # Action 2 with duplicate idempotency key must fail
    action2 = RecoveryAction(
        opportunity_id=opp.id,
        action_type=RecoveryActionType.CREATE_PAYMENT_LINK,
        idempotency_key="idem_key_unique_101",  # duplicate
        policy_approved=True,
        execution_status=ActionExecutionStatus.SUCCESS,
    )
    db_session.add(action2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_processed_webhook_idempotency(db_session: AsyncSession):
    wh1 = ProcessedWebhook(
        provider="razorpay",
        event_id="evt_test_unique_999",
        event_type="payment.failed",
        payload={"dummy": "data"},
    )
    db_session.add(wh1)
    await db_session.commit()

    wh_duplicate = ProcessedWebhook(
        provider="razorpay",
        event_id="evt_test_unique_999",  # duplicate
        event_type="payment.failed",
        payload={"dummy": "data"},
    )
    db_session.add(wh_duplicate)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

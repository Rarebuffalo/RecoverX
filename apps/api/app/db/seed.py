import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    RecoveryDecision,
    RecoveryAction,
    MerchantPolicy,
    AuditEvent,
    ProcessedWebhook,
    AgentRun,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    RecoveryActionType,
    ActionExecutionStatus,
    ActorType,
)
from app.core.logging import logger, setup_logging

# Deterministic UUIDs for development seed data
DEMO_MERCHANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CUST_RAHUL_ID = uuid.UUID("22222222-2222-2222-2222-222222222221")
CUST_PRIYA_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
CUST_AMIT_ID = uuid.UUID("22222222-2222-2222-2222-222222222223")
CUST_VIKRAM_ID = uuid.UUID("22222222-2222-2222-2222-222222222224")
CUST_UNKNOWN_ID = uuid.UUID("22222222-2222-2222-2222-222222222225")

ORDER_A_ID = uuid.UUID("33333333-3333-3333-3333-333333333331")
ORDER_B_ID = uuid.UUID("33333333-3333-3333-3333-333333333332")
ORDER_C_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
ORDER_D_ID = uuid.UUID("33333333-3333-3333-3333-333333333334")
ORDER_E_ID = uuid.UUID("33333333-3333-3333-3333-333333333335")

OPP_A_ID = uuid.UUID("44444444-4444-4444-4444-444444444441")
OPP_B_ID = uuid.UUID("44444444-4444-4444-4444-444444444442")
OPP_C_ID = uuid.UUID("44444444-4444-4444-4444-444444444443")
OPP_D_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
OPP_E_ID = uuid.UUID("44444444-4444-4444-4444-444444444445")


async def run_seeding(session: AsyncSession, force: bool = False):
    if force:
        logger.info("Force flag passed, resetting demo data...")
        await session.execute(delete(ProcessedWebhook))
        await session.execute(delete(AgentRun))
        await session.execute(delete(AuditEvent).where(AuditEvent.merchant_id == DEMO_MERCHANT_ID))
        await session.execute(delete(RecoveryAction))
        await session.execute(delete(RecoveryDecision))
        await session.execute(delete(RecoveryOpportunity))
        await session.execute(delete(PaymentAttempt))
        await session.execute(delete(Order))
        await session.execute(delete(Customer).where(Customer.merchant_id == DEMO_MERCHANT_ID))
        await session.execute(delete(MerchantPolicy).where(MerchantPolicy.merchant_id == DEMO_MERCHANT_ID))
        await session.execute(delete(Merchant).where(Merchant.id == DEMO_MERCHANT_ID))
        await session.commit()

    # Check if demo merchant already exists
    existing_merchant = await session.execute(
        select(Merchant).where(Merchant.id == DEMO_MERCHANT_ID)
    )
    if existing_merchant.scalar_one_or_none():
        logger.info("Demo data already seeded. Skipping.")
        return

    now = datetime.now(timezone.utc)

    # 1. Create Demo Merchant
    merchant = Merchant(
        id=DEMO_MERCHANT_ID,
        name="Apex Digital Store",
        email="finance@apexdigital.com",
        razorpay_account_id="acc_apex_sandbox_01",
        is_active=True,
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=30),
    )
    session.add(merchant)
    await session.flush()

    # 2. Create Merchant Policy
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=DEMO_MERCHANT_ID,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        max_customer_contact_per_day=2,
        escalation_after_failed_attempts=2,
        allowed_actions=["CREATE_PAYMENT_LINK", "SCHEDULE_MANDATE_RETRY", "CUSTOMER_REMINDER_SMS"],
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=30),
    )
    session.add(policy)

    # 3. Create Customers
    cust_rahul = Customer(
        id=CUST_RAHUL_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Rahul Sharma",
        email="rahul.sharma@example.com",
        phone="+919876543210",
        lifetime_value_inr=Decimal("24500.00"),
        total_orders=6,
        successful_orders=5,
        created_at=now - timedelta(days=20),
        updated_at=now,
    )
    cust_priya = Customer(
        id=CUST_PRIYA_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Priya Patel",
        email="priya.patel@example.com",
        phone="+919876543211",
        lifetime_value_inr=Decimal("180000.00"),
        total_orders=12,
        successful_orders=11,
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    cust_amit = Customer(
        id=CUST_AMIT_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Amit Verma",
        email="amit.verma@example.com",
        phone="+919876543212",
        lifetime_value_inr=Decimal("4999.00"),
        total_orders=1,
        successful_orders=1,
        created_at=now - timedelta(days=1),
        updated_at=now,
    )
    cust_vikram = Customer(
        id=CUST_VIKRAM_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Vikram Malhotra",
        email="vikram.m@example.com",
        phone="+919876543213",
        lifetime_value_inr=Decimal("14200.00"),
        total_orders=3,
        successful_orders=2,
        created_at=now - timedelta(days=15),
        updated_at=now,
    )
    cust_unknown = Customer(
        id=CUST_UNKNOWN_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Anonymous Customer",
        email="fraud_alert_99@test.com",
        phone="+919876543214",
        lifetime_value_inr=Decimal("0.00"),
        total_orders=1,
        successful_orders=0,
        created_at=now - timedelta(days=1),
        updated_at=now,
    )
    session.add_all([cust_rahul, cust_priya, cust_amit, cust_vikram, cust_unknown])
    await session.flush()

    # ----------------------------------------------------
    # SCENARIO A: Fresh Failure / Transient Timeout (₹8,499) -> DETECTED / ALLOW
    # ----------------------------------------------------
    order_a = Order(
        id=ORDER_A_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=CUST_RAHUL_ID,
        provider_order_id="order_rzp_mock_a01",
        amount_inr=Decimal("8499.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
        created_at=now - timedelta(minutes=12),
        updated_at=now - timedelta(minutes=10),
    )
    session.add(order_a)
    await session.flush()

    attempt_a = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_A_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_a01_att1",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("8499.00"),
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
        failure_reason="Gateway switch timed out while contacting NPCI UPI bank handle.",
        created_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=10),
    )
    session.add(attempt_a)

    opp_a = RecoveryOpportunity(
        id=OPP_A_ID,
        merchant_id=DEMO_MERCHANT_ID,
        order_id=ORDER_A_ID,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("8499.00"),
        recovered_amount_inr=Decimal("0.00"),
        recovery_score=85,
        attempt_count=0,
        created_at=now - timedelta(minutes=11),
        updated_at=now - timedelta(minutes=11),
    )
    session.add(opp_a)

    # ----------------------------------------------------
    # SCENARIO B: Safety Test / High Ticket (₹45,000) -> ESCALATED
    # ----------------------------------------------------
    order_b = Order(
        id=ORDER_B_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=CUST_PRIYA_ID,
        provider_order_id="order_rzp_mock_b02",
        amount_inr=Decimal("45000.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=1),
    )
    session.add(order_b)
    await session.flush()

    attempt_b1 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_B_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_b02_att1",
        method="card",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("45000.00"),
        failure_code="PAYMENT_CARD_INSUFFICIENT_FUNDS",
        failure_reason="Card account balance insufficient.",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
    )
    attempt_b2 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_B_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_b02_att2",
        method="card",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("45000.00"),
        failure_code="PAYMENT_CARD_INSUFFICIENT_FUNDS",
        failure_reason="Second attempt declined by issuing bank.",
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
    )
    session.add_all([attempt_b1, attempt_b2])

    opp_b = RecoveryOpportunity(
        id=OPP_B_ID,
        merchant_id=DEMO_MERCHANT_ID,
        order_id=ORDER_B_ID,
        status=OpportunityStatus.ESCALATED,
        revenue_at_risk_inr=Decimal("45000.00"),
        recovered_amount_inr=Decimal("0.00"),
        recovery_score=42,
        attempt_count=2,
        last_attempt_at=now - timedelta(hours=1),
        resolved_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=1),
    )
    session.add(opp_b)

    # ----------------------------------------------------
    # SCENARIO C: Successful Recovery (₹4,999) -> RECOVERED / PAID
    # ----------------------------------------------------
    order_c = Order(
        id=ORDER_C_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=CUST_AMIT_ID,
        provider_order_id="order_rzp_mock_c03",
        amount_inr=Decimal("4999.00"),
        currency="INR",
        status=OrderStatus.PAID,
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=4),
    )
    session.add(order_c)
    await session.flush()

    attempt_c1 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_C_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_c03_att1",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("4999.00"),
        failure_code="BAD_REQUEST_USER_CANCELLED",
        failure_reason="Customer dropped out of UPI app drawer.",
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=5),
    )
    attempt_c2 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_C_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_c03_att2_recovered",
        method="upi",
        status=PaymentAttemptStatus.CAPTURED,
        amount_inr=Decimal("4999.00"),
        created_at=now - timedelta(hours=4),
        updated_at=now - timedelta(hours=4),
    )
    session.add_all([attempt_c1, attempt_c2])

    opp_c = RecoveryOpportunity(
        id=OPP_C_ID,
        merchant_id=DEMO_MERCHANT_ID,
        order_id=ORDER_C_ID,
        status=OpportunityStatus.RECOVERED,
        revenue_at_risk_inr=Decimal("4999.00"),
        recovered_amount_inr=Decimal("4999.00"),
        recovery_score=92,
        attempt_count=1,
        last_attempt_at=now - timedelta(hours=4, minutes=30),
        resolved_at=now - timedelta(hours=4),
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=4),
    )
    session.add(opp_c)
    await session.flush()

    # ----------------------------------------------------
    # SCENARIO D: Ambiguous Gateway Timeout (₹3,250) -> INTERVENED / AMBIGUOUS
    # ----------------------------------------------------
    order_d = Order(
        id=ORDER_D_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=CUST_VIKRAM_ID,
        provider_order_id="order_rzp_mock_d04",
        amount_inr=Decimal("3250.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
        created_at=now - timedelta(hours=4),
        updated_at=now - timedelta(hours=3),
    )
    session.add(order_d)
    await session.flush()

    attempt_d1 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_D_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_d04_att1",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("3250.00"),
        failure_code="GATEWAY_NETWORK_TIMEOUT",
        failure_reason="Gateway switch timed out before ACK received.",
        created_at=now - timedelta(hours=4),
        updated_at=now - timedelta(hours=4),
    )
    session.add(attempt_d1)

    opp_d = RecoveryOpportunity(
        id=OPP_D_ID,
        merchant_id=DEMO_MERCHANT_ID,
        order_id=ORDER_D_ID,
        status=OpportunityStatus.INTERVENED,
        revenue_at_risk_inr=Decimal("3250.00"),
        recovered_amount_inr=Decimal("0.00"),
        recovery_score=72,
        attempt_count=1,
        last_attempt_at=now - timedelta(hours=3),
        created_at=now - timedelta(hours=4),
        updated_at=now - timedelta(hours=3),
    )
    session.add(opp_d)

    # ----------------------------------------------------
    # SCENARIO E: Hard / Fraud Decline (₹6,500) -> CLOSED_UNRECOVERED / BLOCK
    # ----------------------------------------------------
    order_e = Order(
        id=ORDER_E_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=CUST_UNKNOWN_ID,
        provider_order_id="order_rzp_mock_e05",
        amount_inr=Decimal("6500.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    session.add(order_e)
    await session.flush()

    attempt_e1 = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=ORDER_E_ID,
        merchant_id=DEMO_MERCHANT_ID,
        provider_payment_id="pay_rzp_mock_e05_att1",
        method="card",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("6500.00"),
        failure_code="PAYMENT_CARD_STOLEN_DECLINE",
        failure_reason="Card reported stolen. Fraud risk threshold exceeded.",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    session.add(attempt_e1)

    opp_e = RecoveryOpportunity(
        id=OPP_E_ID,
        merchant_id=DEMO_MERCHANT_ID,
        order_id=ORDER_E_ID,
        status=OpportunityStatus.CLOSED_UNRECOVERED,
        revenue_at_risk_inr=Decimal("6500.00"),
        recovered_amount_inr=Decimal("0.00"),
        recovery_score=14,
        attempt_count=1,
        last_attempt_at=now - timedelta(days=1),
        resolved_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    session.add(opp_e)
    await session.flush()

    # Add Actions & Audit Events after Opportunities are flushed
    action_b = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=OPP_B_ID,
        action_type=RecoveryActionType.CREATE_PAYMENT_LINK,
        idempotency_key=f"idem_{OPP_B_ID}_attempt_2",
        policy_approved=False,
        policy_rejection_reasons=["AMOUNT_EXCEEDS_AUTO_LIMIT (₹45000 > ₹15000)", "MAX_RETRIES_EXCEEDED (2 >= 2)"],
        execution_status=ActionExecutionStatus.BLOCKED,
        created_at=now - timedelta(hours=1),
    )
    action_c = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=OPP_C_ID,
        action_type=RecoveryActionType.CREATE_PAYMENT_LINK,
        idempotency_key=f"idem_{OPP_C_ID}_attempt_1",
        policy_approved=True,
        execution_status=ActionExecutionStatus.SUCCEEDED,
        provider_action_id="plink_rzp_mock_c03_recovered",
        executed_at=now - timedelta(hours=4, minutes=30),
        created_at=now - timedelta(hours=4, minutes=30),
    )
    action_d = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=OPP_D_ID,
        action_type=RecoveryActionType.CREATE_PAYMENT_LINK,
        idempotency_key=f"idem_{OPP_D_ID}_attempt_1",
        policy_approved=True,
        execution_status=ActionExecutionStatus.AMBIGUOUS,
        error_category="GATEWAY_NETWORK_TIMEOUT",
        error_message="Gateway switch connection timed out before ACK received. Blind retries blocked.",
        created_at=now - timedelta(hours=3),
    )
    audit_c = AuditEvent(
        id=uuid.uuid4(),
        merchant_id=DEMO_MERCHANT_ID,
        opportunity_id=OPP_C_ID,
        actor_type=ActorType.SYSTEM,
        event_type="REVENUE_RECOVERED",
        event_summary="Order successfully recovered: ₹4,999.00 captured via recovery link plink_rzp_mock_c03_recovered",
        event_data={"recovered_amount_inr": "4999.00", "provider_payment_id": "pay_rzp_mock_c03_att2_recovered"},
        created_at=now - timedelta(hours=4),
    )
    session.add_all([action_b, action_c, action_d, audit_c])
    await session.commit()
    logger.info("Successfully seeded RecoverX demo database with Scenarios A, B, C, D, and E.")


async def seed_database(force: bool = False):
    setup_logging()
    logger.info("Starting RecoverX database seeding...")
    async with AsyncSessionLocal() as session:
        await run_seeding(session, force=force)


if __name__ == "__main__":
    asyncio.run(seed_database())

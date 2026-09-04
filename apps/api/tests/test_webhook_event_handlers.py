import json
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    Merchant,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    AuditEvent,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    ActorType,
)
from app.services.webhook_verifier import WebhookSignatureVerifier


@pytest.mark.asyncio
async def test_payment_failed_event_processing(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Apex Store", email="apex_wh@example.com", razorpay_account_id="acc_apex_01")
    db_session.add(merchant)
    await db_session.commit()

    payload = {
        "entity": "event",
        "account_id": "acc_apex_01",
        "event": "payment.failed",
        "event_id": "evt_fail_101",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_fail_001",
                    "order_id": "order_fail_001",
                    "amount": 849900,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "error_code": "BAD_REQUEST_GATEWAY_TIMEOUT",
                    "error_description": "Bank switch did not respond in time on UPI intent.",
                    "email": "rahul@example.com",
                    "contact": "+919876543210",
                }
            }
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    sig = WebhookSignatureVerifier.compute_signature(raw_body, secret)

    res = await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    # 1. Verify Order created
    order_res = await db_session.execute(
        select(Order).where(Order.provider_order_id == "order_fail_001")
    )
    order = order_res.scalar_one()
    assert order.status == OrderStatus.ATTEMPTED
    assert order.amount_inr == Decimal("8499.00")

    # 2. Verify Payment Attempt created
    attempt_res = await db_session.execute(
        select(PaymentAttempt).where(PaymentAttempt.provider_payment_id == "pay_fail_001")
    )
    attempt = attempt_res.scalar_one()
    assert attempt.status == PaymentAttemptStatus.FAILED
    assert attempt.failure_code == "BAD_REQUEST_GATEWAY_TIMEOUT"
    assert attempt.order_id == order.id

    # 3. Verify Recovery Opportunity created in DETECTED state
    opp_res = await db_session.execute(
        select(RecoveryOpportunity).where(RecoveryOpportunity.order_id == order.id)
    )
    opp = opp_res.scalar_one()
    assert opp.status == OpportunityStatus.DETECTED
    assert opp.revenue_at_risk_inr == Decimal("8499.00")
    assert opp.recovered_amount_inr == Decimal("0.00")

    # 4. Verify Audit Events recorded
    audit_res = await db_session.execute(
        select(AuditEvent).where(AuditEvent.merchant_id == merchant.id)
    )
    audits = audit_res.scalars().all()
    assert len(audits) >= 1


@pytest.mark.asyncio
async def test_payment_captured_event_processing(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Apex Store 2", email="apex_wh2@example.com", razorpay_account_id="acc_apex_02")
    db_session.add(merchant)
    await db_session.commit()

    # First send failed payment
    fail_payload = {
        "entity": "event",
        "account_id": "acc_apex_02",
        "event": "payment.failed",
        "event_id": "evt_fail_201",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_201_att1",
                    "order_id": "order_sync_201",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "email": "amit@example.com",
                }
            }
        },
    }
    raw_fail = json.dumps(fail_payload).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_fail,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_fail, secret)},
    )

    # Now send payment.captured for attempt 2 on the SAME order
    cap_payload = {
        "entity": "event",
        "account_id": "acc_apex_02",
        "event": "payment.captured",
        "event_id": "evt_cap_202",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_201_att2_captured",
                    "order_id": "order_sync_201",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "captured",
                    "method": "upi",
                    "email": "amit@example.com",
                }
            }
        },
    }
    raw_cap = json.dumps(cap_payload).encode("utf-8")
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_cap,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_cap, secret)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    # Verify Order is PAID
    order = (await db_session.execute(select(Order).where(Order.provider_order_id == "order_sync_201"))).scalar_one()
    assert order.status == OrderStatus.PAID

    # Verify Opportunity is transitioned to RECOVERED (preemption/recovery)
    opp = (await db_session.execute(select(RecoveryOpportunity).where(RecoveryOpportunity.order_id == order.id))).scalar_one()
    assert opp.status == OpportunityStatus.RECOVERED
    assert opp.recovered_amount_inr == Decimal("4999.00")
    assert opp.resolved_at is not None


@pytest.mark.asyncio
async def test_unsupported_event_handling(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Apex Store 3", email="apex_wh3@example.com", razorpay_account_id="acc_apex_03")
    db_session.add(merchant)
    await db_session.commit()

    payload = {
        "entity": "event",
        "account_id": "acc_apex_03",
        "event": "refund.created",
        "event_id": "evt_unsupported_999",
        "payload": {},
    }
    raw = json.dumps(payload).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw, secret)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ignored_unsupported"


@pytest.mark.asyncio
async def test_payment_link_paid_real_razorpay_reconciliation_regression(client: AsyncClient, db_session: AsyncSession):
    """Regression test reproducing exact Razorpay test mode payment link flow where:
    - Order has initial merchant provider_order_id (e.g. 'order_rzp_mock_a01')
    - Payment Link has real Razorpay ID 'plink_real_test_999' and separate internal 'order_plink_999'
    - Webhook event for payment_link.paid must reconcile Opportunity to RECOVERED and Action to SUCCEEDED.
    """
    import uuid
    from app.models import RecoveryAction, ActionExecutionStatus

    merchant = Merchant(name="Razorpay Store", email="rzp_test@example.com", razorpay_account_id="acc_rzp_test_01")
    db_session.add(merchant)
    await db_session.flush()

    from app.models import Customer
    customer = Customer(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        email="rahul@example.com",
        name="Rahul Sharma",
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_rzp_mock_a01",
        amount_inr=Decimal("8499.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        id=uuid.UUID("44444444-4444-4444-4444-444444444441"),
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.INTERVENED,
        revenue_at_risk_inr=Decimal("8499.00"),
        recovered_amount_inr=Decimal("0.00"),
        attempt_count=1,
    )
    db_session.add(opp)
    await db_session.flush()

    action = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=opp.id,
        action_type="CREATE_RECOVERY_PAYMENT_LINK",
        idempotency_key="recovery:44444444-4444-4444-4444-444444444441:attempt:1",
        provider_action_id="plink_real_test_999",
        payment_link_url="https://rzp.io/i/real_test_link",
        policy_approved=True,
        execution_status=ActionExecutionStatus.SUCCEEDED,
    )
    db_session.add(action)
    await db_session.commit()

    # Razorpay Webhook Payload for payment_link.paid
    plink_payload = {
        "entity": "event",
        "account_id": "acc_rzp_test_01",
        "event": "payment_link.paid",
        "event_id": "evt_plink_real_test_01",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_real_test_999",
                    "amount": 849900,
                    "amount_paid": 849900,
                    "currency": "INR",
                    "status": "paid",
                    "order_id": "order_internal_razorpay_plink_999",
                    "reference_id": "rec_real_test_ref",
                    "notes": {
                        "opportunity_id": "44444444-4444-4444-4444-444444444441",
                        "action_id": str(action.id),
                        "merchant_id": str(merchant.id),
                    },
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_real_test_888",
                    "amount": 849900,
                    "currency": "INR",
                    "status": "captured",
                    "order_id": "order_internal_razorpay_plink_999",
                    "method": "upi",
                    "notes": {
                        "opportunity_id": "44444444-4444-4444-4444-444444444441",
                    },
                }
            },
        },
    }

    raw = json.dumps(plink_payload).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw, secret)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    # 1. Verify Opportunity is RECOVERED
    await db_session.refresh(opp)
    assert opp.status == OpportunityStatus.RECOVERED
    assert opp.recovered_amount_inr == Decimal("8499.00")
    assert opp.resolved_at is not None

    # 2. Verify Order is PAID
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID

    # 3. Verify Payment Attempt captured
    attempt = (await db_session.execute(
        select(PaymentAttempt).where(PaymentAttempt.provider_payment_id == "pay_real_test_888")
    )).scalar_one()
    assert attempt.status == PaymentAttemptStatus.CAPTURED
    assert attempt.order_id == order.id

    # 4. Verify Action is SUCCEEDED
    await db_session.refresh(action)
    assert action.execution_status == ActionExecutionStatus.SUCCEEDED
    assert action.provider_action_id == "plink_real_test_999"

    # 5. Verify REVENUE_RECOVERED audit event exists
    audit = (await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.opportunity_id == opp.id,
            AuditEvent.event_type == "REVENUE_RECOVERED",
        )
    )).scalar_one_or_none()
    assert audit is not None


@pytest.mark.asyncio
async def test_reconcile_opportunity_api_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verifies that calling POST /api/v1/opportunities/{id}/reconcile safely resolves an unreconciled opportunity."""
    import uuid
    from app.models import RecoveryAction, ActionExecutionStatus

    merchant = Merchant(name="Reconcile Store", email="rec_test@example.com", razorpay_account_id="acc_rec_test_01")
    db_session.add(merchant)
    await db_session.flush()

    from app.models import Customer
    customer = Customer(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        email="rec_cust@example.com",
        name="Reconcile Customer",
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_rec_01",
        amount_inr=Decimal("8499.00"),
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        id=uuid.UUID("44444444-4444-4444-4444-444444444442"),
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.INTERVENED,
        revenue_at_risk_inr=Decimal("8499.00"),
        recovered_amount_inr=Decimal("0.00"),
        attempt_count=1,
    )
    db_session.add(opp)
    await db_session.flush()

    action = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=opp.id,
        action_type="CREATE_RECOVERY_PAYMENT_LINK",
        idempotency_key="recovery:44444444-4444-4444-4444-444444444442:attempt:1",
        provider_action_id="plink_audit_match_123",
        payment_link_url="https://rzp.io/i/audit_match",
        policy_approved=True,
        execution_status=ActionExecutionStatus.SUCCEEDED,
    )
    db_session.add(action)

    # Insert an audit event matching this plink
    db_session.add(AuditEvent(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        opportunity_id=None,
        actor_type=ActorType.SYSTEM,
        event_type="PAYMENT_LINK_PAID_PROCESSED",
        event_summary="Processed payment_link.paid for plink_audit_match_123",
        event_data={
            "provider_plink_id": "plink_audit_match_123",
            "amount_inr": "8499.00",
        },
    ))
    await db_session.commit()

    # Call reconcile endpoint
    res = await client.post(f"/api/v1/opportunities/{opp.id}/reconcile")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "reconciled"
    assert data["recovered_amount_inr"] == 8499.0

    # Verify database state
    await db_session.refresh(opp)
    assert opp.status == OpportunityStatus.RECOVERED
    assert opp.recovered_amount_inr == Decimal("8499.00")


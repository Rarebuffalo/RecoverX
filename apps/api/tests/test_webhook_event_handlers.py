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

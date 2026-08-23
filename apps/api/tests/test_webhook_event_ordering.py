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
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
)
from app.services.webhook_verifier import WebhookSignatureVerifier


@pytest.mark.asyncio
async def test_event_ordering_captured_before_failed(client: AsyncClient, db_session: AsyncSession):
    """If payment.captured arrives before a late/retried payment.failed, order must remain PAID."""
    merchant = Merchant(name="Order Store", email="order_test@example.com", razorpay_account_id="acc_ordering_01")
    db_session.add(merchant)
    await db_session.commit()

    secret = "dev_razorpay_webhook_secret_123"

    # 1. First payment.captured arrives
    cap_payload = {
        "entity": "event",
        "account_id": "acc_ordering_01",
        "event": "payment.captured",
        "event_id": "evt_order_cap_1",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_captured_early",
                    "order_id": "order_precedence_01",
                    "amount": 750000,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }
    raw_cap = json.dumps(cap_payload).encode("utf-8")
    await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_cap,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_cap, secret)},
    )

    # 2. Out-of-order late payment.failed arrives for a previous failed attempt on same order
    fail_payload = {
        "entity": "event",
        "account_id": "acc_ordering_01",
        "event": "payment.failed",
        "event_id": "evt_order_fail_late",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_late",
                    "order_id": "order_precedence_01",
                    "amount": 750000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "GATEWAY_TIMEOUT",
                }
            }
        },
    }
    raw_fail = json.dumps(fail_payload).encode("utf-8")
    await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_fail,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_fail, secret)},
    )

    # 3. Verify Order status is still PAID (not downgraded to attempted)
    order = (await db_session.execute(
        select(Order).where(Order.provider_order_id == "order_precedence_01")
    )).scalar_one()
    assert order.status == OrderStatus.PAID

    # 4. Verify Payment Attempt 1 and 2 exist
    attempts = (await db_session.execute(
        select(PaymentAttempt).where(PaymentAttempt.order_id == order.id)
    )).scalars().all()
    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_tenant_webhook_isolation(client: AsyncClient, db_session: AsyncSession):
    """Events for Merchant A must not collide or overwrite Merchant B's order IDs."""
    mA = Merchant(name="Merchant A", email="ma@example.com", razorpay_account_id="acc_tenant_A")
    mB = Merchant(name="Merchant B", email="mb@example.com", razorpay_account_id="acc_tenant_B")
    db_session.add_all([mA, mB])
    await db_session.commit()

    secret = "dev_razorpay_webhook_secret_123"

    # Send event for Merchant A
    payload_A = {
        "entity": "event",
        "account_id": "acc_tenant_A",
        "event": "payment.failed",
        "event_id": "evt_tenant_A_01",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_tenant_A_1",
                    "order_id": "order_shared_code",
                    "amount": 100000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
    }
    raw_A = json.dumps(payload_A).encode("utf-8")
    await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_A,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_A, secret)},
    )

    # Send event for Merchant B with identical provider order_id string
    payload_B = {
        "entity": "event",
        "account_id": "acc_tenant_B",
        "event": "payment.failed",
        "event_id": "evt_tenant_B_01",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_tenant_B_1",
                    "order_id": "order_shared_code",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
    }
    raw_B = json.dumps(payload_B).encode("utf-8")
    await client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_B,
        headers={"X-Razorpay-Signature": WebhookSignatureVerifier.compute_signature(raw_B, secret)},
    )

    # Verify two distinct orders exist, each scoped to their respective merchant
    orders = (await db_session.execute(
        select(Order).where(Order.provider_order_id == "order_shared_code")
    )).scalars().all()
    assert len(orders) == 2
    merchant_ids = {o.merchant_id for o in orders}
    assert mA.id in merchant_ids
    assert mB.id in merchant_ids

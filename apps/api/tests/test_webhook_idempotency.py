import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, ProcessedWebhook
from app.services.webhook_verifier import WebhookSignatureVerifier
from sqlalchemy import select


@pytest.mark.asyncio
async def test_webhook_idempotency_same_event_twice(client: AsyncClient, db_session: AsyncSession):
    # Setup Merchant
    merchant = Merchant(name="Idem Store", email="idem@example.com", razorpay_account_id="acc_idem_01")
    db_session.add(merchant)
    await db_session.commit()

    webhook_payload = {
        "entity": "event",
        "account_id": "acc_idem_01",
        "event": "payment.failed",
        "event_id": "evt_duplicate_test_100",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_idem_01",
                    "order_id": "order_idem_01",
                    "amount": 500000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "error_code": "BAD_REQUEST_GATEWAY_TIMEOUT",
                    "email": "buyer@example.com",
                }
            }
        },
    }

    raw_body = json.dumps(webhook_payload).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    signature = WebhookSignatureVerifier.compute_signature(raw_body, secret)
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": "evt_duplicate_test_100",
    }

    # 1. First event submission -> 200 OK & processed
    res1 = await client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"
    assert res1.json()["event_id"] == "evt_duplicate_test_100"

    # 2. Second submission with EXACT SAME event_id -> 200 OK & already_processed
    res2 = await client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_processed"
    assert res2.json()["event_id"] == "evt_duplicate_test_100"

    # Verify only 1 record exists in processed_webhooks
    query = select(ProcessedWebhook).where(ProcessedWebhook.event_id == "evt_duplicate_test_100")
    results = (await db_session.execute(query)).scalars().all()
    assert len(results) == 1


@pytest.mark.asyncio
async def test_webhook_different_event_ids(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Multi Event Store", email="multi_evt@example.com", razorpay_account_id="acc_multi_01")
    db_session.add(merchant)
    await db_session.commit()

    secret = "dev_razorpay_webhook_secret_123"

    for i in [1, 2]:
        webhook_payload = {
            "entity": "event",
            "account_id": "acc_multi_01",
            "event": "payment.failed",
            "event_id": f"evt_diff_{i}",
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_diff_{i}",
                        "order_id": f"order_diff_{i}",
                        "amount": 200000,
                        "currency": "INR",
                        "status": "failed",
                    }
                }
            },
        }
        raw_body = json.dumps(webhook_payload).encode("utf-8")
        sig = WebhookSignatureVerifier.compute_signature(raw_body, secret)
        res = await client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": f"evt_diff_{i}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "processed"

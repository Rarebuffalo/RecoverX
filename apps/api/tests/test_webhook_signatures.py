import json
import pytest
from httpx import AsyncClient
from app.services.webhook_verifier import WebhookSignatureVerifier


def test_signature_verifier_unit():
    secret = "test_secret_12345"
    payload = b'{"event":"payment.failed","id":"evt_1"}'

    # 1. Valid signature
    sig = WebhookSignatureVerifier.compute_signature(payload, secret)
    assert WebhookSignatureVerifier.verify(payload, sig, secret) is True

    # 2. Invalid signature
    assert WebhookSignatureVerifier.verify(payload, "invalid_signature_hex", secret) is False

    # 3. Modified body (payload tampered with after signing)
    tampered_payload = b'{"event":"payment.failed","id":"evt_1","tampered":true}'
    assert WebhookSignatureVerifier.verify(tampered_payload, sig, secret) is False

    # 4. Missing signature
    assert WebhookSignatureVerifier.verify(payload, None, secret) is False
    assert WebhookSignatureVerifier.verify(payload, "", secret) is False

    # 5. Wrong secret
    assert WebhookSignatureVerifier.verify(payload, sig, "wrong_secret") is False


@pytest.mark.asyncio
async def test_webhook_endpoint_signature_verification(client: AsyncClient):
    payload = json.dumps({"event": "payment.failed", "payload": {}}).encode("utf-8")
    secret = "dev_razorpay_webhook_secret_123"
    valid_sig = WebhookSignatureVerifier.compute_signature(payload, secret)

    # 1. Missing signature -> 401
    res1 = await client.post("/api/v1/webhooks/razorpay", content=payload)
    assert res1.status_code == 401

    # 2. Invalid signature -> 401
    res2 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=payload,
        headers={"X-Razorpay-Signature": "bad_signature"},
    )
    assert res2.status_code == 401

    # 3. Valid signature on empty body -> 400
    empty_sig = WebhookSignatureVerifier.compute_signature(b"", secret)
    res3 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=b"",
        headers={"X-Razorpay-Signature": empty_sig},
    )
    assert res3.status_code == 400

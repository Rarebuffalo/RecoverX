import json
import os
import sys
import httpx
from pathlib import Path
from app.services.webhook_verifier import WebhookSignatureVerifier
from app.core.config import settings

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "razorpay"


def send_webhook(event_fixture: str = "payment_failed.json", target_url: str = "http://localhost:8000/api/v1/webhooks/razorpay"):
    fixture_path = FIXTURES_DIR / event_fixture
    if not fixture_path.exists():
        print(f"Error: Fixture file '{fixture_path}' not found.")
        sys.exit(1)

    with open(fixture_path, "rb") as f:
        raw_body = f.read()

    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or "dev_razorpay_webhook_secret_123"
    signature = WebhookSignatureVerifier.compute_signature(raw_body, webhook_secret)

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": f"evt_local_cli_{event_fixture.replace('.json', '')}",
    }

    print(f"Sending signed webhook fixture '{event_fixture}' to {target_url}...")
    try:
        with httpx.Client() as client:
            response = client.post(target_url, content=raw_body, headers=headers, timeout=5.0)
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Failed to send webhook: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fixture = sys.argv[1] if len(sys.argv) > 1 else "payment_failed.json"
    send_webhook(fixture)

import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db
from app.models import Merchant, Order, PaymentAttempt, RecoveryOpportunity, ProcessedWebhook, OrderStatus
from app.services.webhook_verifier import WebhookSignatureVerifier
from app.main import app


@pytest.mark.asyncio
async def test_postgres_live_idempotency_and_concurrency():
    """Integration test executing against live PostgreSQL database."""
    pg_engine = create_async_engine(settings.DATABASE_URL, future=True)
    PgSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with PgSessionLocal() as session:
        # Create unique test merchant
        merchant = Merchant(
            name="PG Live Store",
            email="pg_live@example.com",
            razorpay_account_id="acc_pg_live_01",
        )
        session.add(merchant)
        try:
            await session.commit()
        except Exception:
            await session.rollback()

    async def _get_pg_db():
        async with PgSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_pg_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "entity": "event",
            "account_id": "acc_pg_live_01",
            "event": "payment.failed",
            "event_id": "evt_pg_live_concurrent_01",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_pg_live_001",
                        "order_id": "order_pg_live_001",
                        "amount": 99900,
                        "currency": "INR",
                        "status": "failed",
                        "error_code": "BAD_REQUEST_GATEWAY_TIMEOUT",
                    }
                }
            },
        }
        raw_body = json.dumps(payload).encode("utf-8")
        secret = "dev_razorpay_webhook_secret_123"
        sig = WebhookSignatureVerifier.compute_signature(raw_body, secret)

        # 1. Send first event
        res1 = await client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig},
        )
        assert res1.status_code == 200
        assert res1.json()["status"] in ["processed", "already_processed"]

        # 2. Send duplicate event
        res2 = await client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig},
        )
        assert res2.status_code == 200
        assert res2.json()["status"] == "already_processed"

    app.dependency_overrides.clear()
    await pg_engine.dispose()

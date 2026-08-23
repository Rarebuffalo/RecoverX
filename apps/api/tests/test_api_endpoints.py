import uuid
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    MerchantPolicy,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
)


@pytest.mark.asyncio
async def test_get_merchant_api(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Apex Store", email="apex@example.com")
    db_session.add(merchant)
    await db_session.commit()

    policy = MerchantPolicy(
        merchant_id=merchant.id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("10000.00"),
        max_customer_contact_per_day=2,
        escalation_after_failed_attempts=2,
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )
    db_session.add(policy)
    await db_session.commit()

    response = await client.get(f"/api/v1/merchants/{merchant.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Apex Store"
    assert data["email"] == "apex@example.com"
    assert data["policy"]["auto_recovery_enabled"] is True
    assert data["policy"]["max_retry_attempts"] == 2


@pytest.mark.asyncio
async def test_get_order_and_attempts_api(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Order API Store", email="order_api@example.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Alice", email="alice@example.com")
    db_session.add(customer)
    await db_session.commit()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_inr=Decimal("7999.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.commit()

    attempt = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_api_1",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("7999.00"),
    )
    db_session.add(attempt)
    await db_session.commit()

    # 1. Get Order Detail
    response = await client.get(f"/api/v1/orders/{order.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["amount_inr"] == "7999.00"
    assert data["status"] == "attempted"
    assert data["customer"]["name"] == "Alice"
    assert len(data["payment_attempts"]) == 1

    # 2. Get Order Payment Attempts
    attempts_response = await client.get(f"/api/v1/orders/{order.id}/payment-attempts")
    assert attempts_response.status_code == 200
    attempts_data = attempts_response.json()
    assert len(attempts_data) == 1
    assert attempts_data[0]["provider_payment_id"] == "pay_api_1"
    assert attempts_data[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_get_opportunity_api(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Opp API Store", email="opp_api@example.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, email="opp_api_cust@example.com")
    db_session.add(customer)
    await db_session.commit()

    order = Order(merchant_id=merchant.id, customer_id=customer.id, amount_inr=Decimal("8499.00"))
    db_session.add(order)
    await db_session.commit()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("8499.00"),
        recovery_score=88,
    )
    db_session.add(opp)
    await db_session.commit()

    response = await client.get(f"/api/v1/opportunities/{opp.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DETECTED"
    assert data["revenue_at_risk_inr"] == "8499.00"
    assert data["recovery_score"] == 88
    assert data["order"]["amount_inr"] == "8499.00"


@pytest.mark.asyncio
async def test_api_404_not_found(client: AsyncClient):
    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/merchants/{random_id}")
    assert resp.status_code == 404
    resp = await client.get(f"/api/v1/orders/{random_id}")
    assert resp.status_code == 404
    resp = await client.get(f"/api/v1/opportunities/{random_id}")
    assert resp.status_code == 404

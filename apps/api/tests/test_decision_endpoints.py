import uuid
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer, Order, PaymentAttempt, RecoveryOpportunity, MerchantPolicy, OrderStatus, PaymentAttemptStatus, OpportunityStatus


@pytest.mark.asyncio
async def test_opportunity_decision_apis(client: AsyncClient, db_session: AsyncSession):
    # Setup test entities
    merchant = Merchant(name="API Test Store", email="api@example.com", razorpay_account_id="acc_api_01")
    db_session.add(merchant)
    await db_session.flush()

    policy = MerchantPolicy(
        merchant_id=merchant.id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_RECOVERY_PAYMENT_LINK"],
    )
    customer = Customer(
        merchant_id=merchant.id,
        email="buyer_api@example.com",
        lifetime_value_inr=Decimal("25000.00"),
        total_orders=5,
        successful_orders=4,
    )
    db_session.add_all([policy, customer])
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_api_test_01",
        amount_inr=Decimal("6500.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    attempt = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_api_test_att1",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("6500.00"),
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
        failure_reason="Gateway timeout on bank switch",
    )
    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("6500.00"),
        attempt_count=0,
    )
    db_session.add_all([attempt, opp])
    await db_session.commit()

    opp_id = str(opp.id)

    # 1. GET /score
    res_score = await client.get(f"/api/v1/opportunities/{opp_id}/score")
    assert res_score.status_code == 200
    data_score = res_score.json()
    assert data_score["opportunity_id"] == opp_id
    assert data_score["score"] >= 80
    assert data_score["score_band"] == "HIGH"
    assert data_score["failure_category"] == "TRANSIENT"
    assert "base_score" in data_score["feature_contributions"]

    # 2. GET /eligibility
    res_elig = await client.get(f"/api/v1/opportunities/{opp_id}/eligibility")
    assert res_elig.status_code == 200
    data_elig = res_elig.json()
    assert data_elig["outcome"] == "AUTO_RECOVER"
    assert data_elig["eligible"] is True
    assert data_elig["recommended_action_class"] == "CREATE_RECOVERY_PAYMENT_LINK"

    # 3. GET /policy-decision
    res_pol = await client.get(f"/api/v1/opportunities/{opp_id}/policy-decision?proposed_action=CREATE_RECOVERY_PAYMENT_LINK")
    assert res_pol.status_code == 200
    data_pol = res_pol.json()
    assert data_pol["decision"] == "ALLOW"
    assert data_pol["policy_version"] == "v1"
    assert "POLICY_APPROVED" in data_pol["reason_codes"]

    # 4. POST /evaluate (persists decision record)
    res_eval = await client.post(f"/api/v1/opportunities/{opp_id}/evaluate?proposed_action=CREATE_RECOVERY_PAYMENT_LINK")
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    assert data_eval["score"]["score"] == data_score["score"]
    assert data_eval["eligibility"]["outcome"] == "AUTO_RECOVER"
    assert data_eval["policy_decision"]["decision"] == "ALLOW"

import uuid
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Merchant, Customer, Order, PaymentAttempt, RecoveryOpportunity, MerchantPolicy, AgentRun, RecoveryDecision, OrderStatus, PaymentAttemptStatus, OpportunityStatus


@pytest.mark.asyncio
async def test_agent_evaluate_and_decisions_api(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="Agent Store", email="agent_test@example.com", razorpay_account_id="acc_agent_01")
    db_session.add(merchant)
    await db_session.flush()

    policy = MerchantPolicy(
        merchant_id=merchant.id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_RECOVERY_PAYMENT_LINK", "CREATE_PAYMENT_LINK"],
    )
    customer = Customer(
        merchant_id=merchant.id,
        email="agent_cust@example.com",
        lifetime_value_inr=Decimal("30000.00"),
        total_orders=6,
        successful_orders=5,
    )
    db_session.add_all([policy, customer])
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_agent_01",
        amount_inr=Decimal("7500.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    attempt = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_agent_01",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("7500.00"),
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
        failure_reason="Gateway switch timeout",
    )
    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("7500.00"),
        attempt_count=0,
    )
    db_session.add_all([attempt, opp])
    await db_session.commit()

    opp_id = str(opp.id)

    # 1. POST /agent-evaluate
    res_eval = await client.post(f"/api/v1/opportunities/{opp_id}/agent-evaluate")
    assert res_eval.status_code == 200
    data = res_eval.json()

    assert data["opportunity_id"] == opp_id
    assert data["provider"] == "mock"
    assert data["status"] == "SUCCESS"
    assert data["ai_proposal"]["recommended_action"] in ["CREATE_RECOVERY_PAYMENT_LINK", "CREATE_PAYMENT_LINK"]
    assert data["ai_proposal"]["confidence"] >= 0.80
    assert data["policy_decision"]["decision"] == "ALLOW"

    # Verify AgentRun was stored
    runs = (await db_session.execute(select(AgentRun).where(AgentRun.opportunity_id == opp.id))).scalars().all()
    assert len(runs) >= 1
    assert runs[0].provider == "mock"

    # Verify RecoveryDecision was stored
    decisions = (await db_session.execute(select(RecoveryDecision).where(RecoveryDecision.opportunity_id == opp.id))).scalars().all()
    assert len(decisions) >= 1
    assert decisions[0].diagnosis_category == "TRANSIENT_PAYMENT_FAILURE"

    # 2. GET /agent-decisions
    res_dec = await client.get(f"/api/v1/opportunities/{opp_id}/agent-decisions")
    assert res_dec.status_code == 200
    dec_list = res_dec.json()
    assert len(dec_list) >= 1
    assert dec_list[0]["diagnosis_category"] == "TRANSIENT_PAYMENT_FAILURE"

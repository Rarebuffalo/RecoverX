import uuid
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer, Order, PaymentAttempt, RecoveryOpportunity, MerchantPolicy, OrderStatus, PaymentAttemptStatus, OpportunityStatus


@pytest.mark.asyncio
async def test_execute_opportunity_and_simulation_api(client: AsyncClient, db_session: AsyncSession):
    merchant = Merchant(name="API Exec Store", email="api_exec@example.com", razorpay_account_id="acc_mock_merchant_01")
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
        email="api_exec_cust@example.com",
        lifetime_value_inr=Decimal("20000.00"),
        total_orders=4,
        successful_orders=4,
    )
    db_session.add_all([policy, customer])
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_api_exec_01",
        amount_inr=Decimal("6200.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    attempt = PaymentAttempt(
        order_id=order.id,
        merchant_id=merchant.id,
        provider_payment_id="pay_api_exec_01",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        amount_inr=Decimal("6200.00"),
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
        failure_reason="Gateway switch timeout",
    )
    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("6200.00"),
        attempt_count=0,
    )
    db_session.add_all([attempt, opp])
    await db_session.commit()

    opp_id = str(opp.id)

    # 1. POST /execute
    res_exec = await client.post(f"/api/v1/opportunities/{opp_id}/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["execution_status"] == "SUCCEEDED"
    assert exec_data["payment_link_url"].startswith("https://rzp.io/i/mock_")
    assert exec_data["provider_action_id"].startswith("plink_mock_")

    # 2. GET /actions
    res_actions = await client.get(f"/api/v1/opportunities/{opp_id}/actions")
    assert res_actions.status_code == 200
    actions_list = res_actions.json()
    assert len(actions_list) >= 1
    assert actions_list[0]["execution_status"] == "SUCCEEDED"

    # 3. POST /developer/simulate-payment-success
    res_sim = await client.post(
        "/api/v1/developer/simulate-payment-success",
        json={"opportunity_id": opp_id, "amount_inr": 6200.0},
    )
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["opportunity_status"] == "RECOVERED"
    assert sim_data["recovered_amount_inr"] == 6200.0

import uuid
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer, Order, RecoveryOpportunity, RecoveryAction, OrderStatus, OpportunityStatus
from app.services.outcome.outcome_service import RecoveryOutcomeService


@pytest.mark.asyncio
async def test_recovery_outcome_full_and_duplicate_prevention(db_session: AsyncSession):
    merchant = Merchant(name="Outcome Store", email="outcome@example.com", razorpay_account_id="acc_out_01")
    db_session.add(merchant)
    await db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        email="outcome_cust@example.com",
        lifetime_value_inr=Decimal("20000.00"),
        total_orders=3,
        successful_orders=3,
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_inr=Decimal("8499.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.INTERVENED,
        revenue_at_risk_inr=Decimal("8499.00"),
        recovered_amount_inr=Decimal("0.00"),
    )
    db_session.add(opp)
    await db_session.commit()

    # 1. First Payment Capture (Full Recovery)
    updated_opp = await RecoveryOutcomeService.record_payment_recovery(
        db_session,
        order_id=order.id,
        provider_payment_id="pay_out_101",
        amount_inr=Decimal("8499.00"),
    )
    assert updated_opp.status == OpportunityStatus.RECOVERED
    assert updated_opp.recovered_amount_inr == Decimal("8499.00")

    # 2. Duplicate Captured Event does NOT increase revenue
    dup_opp = await RecoveryOutcomeService.record_payment_recovery(
        db_session,
        order_id=order.id,
        provider_payment_id="pay_out_101",
        amount_inr=Decimal("8499.00"),
    )
    assert dup_opp.recovered_amount_inr == Decimal("8499.00")

    # 3. Check Recovery Metrics
    metrics = await RecoveryOutcomeService.get_recovery_metrics(db_session)
    assert metrics["recovered_opportunities"] >= 1
    assert metrics["total_recovered_revenue_inr"] >= 8499.0

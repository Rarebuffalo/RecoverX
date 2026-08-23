import pytest
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
)


@pytest.mark.asyncio
async def test_one_order_multiple_payment_attempts_relationship(db_session: AsyncSession):
    merchant = Merchant(name="Multi Attempt Store", email="multi@example.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, email="multi_buyer@example.com")
    db_session.add(customer)
    await db_session.commit()

    # Create 1 Order
    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_inr=Decimal("8499.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.commit()

    # Create 3 distinct payment attempts for the SAME order
    for i, (method, status, p_id) in enumerate([
        ("card", PaymentAttemptStatus.FAILED, "pay_att_1"),
        ("netbanking", PaymentAttemptStatus.FAILED, "pay_att_2"),
        ("upi", PaymentAttemptStatus.CAPTURED, "pay_att_3"),
    ]):
        attempt = PaymentAttempt(
            order_id=order.id,
            merchant_id=merchant.id,
            provider_payment_id=p_id,
            method=method,
            status=status,
            amount_inr=Decimal("8499.00"),
        )
        db_session.add(attempt)

    await db_session.commit()

    # Query order with loaded payment_attempts
    query = (
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.payment_attempts))
    )
    result = await db_session.execute(query)
    fetched_order = result.scalar_one()

    assert len(fetched_order.payment_attempts) == 3
    assert fetched_order.payment_attempts[0].provider_payment_id == "pay_att_1"
    assert fetched_order.payment_attempts[0].status == PaymentAttemptStatus.FAILED
    assert fetched_order.payment_attempts[1].provider_payment_id == "pay_att_2"
    assert fetched_order.payment_attempts[2].provider_payment_id == "pay_att_3"
    assert fetched_order.payment_attempts[2].status == PaymentAttemptStatus.CAPTURED


@pytest.mark.asyncio
async def test_recovery_opportunity_order_level_relationship(db_session: AsyncSession):
    merchant = Merchant(name="Opp Store", email="opp@example.com")
    db_session.add(merchant)
    await db_session.commit()

    customer = Customer(merchant_id=merchant.id, email="opp_buyer@example.com")
    db_session.add(customer)
    await db_session.commit()

    order = Order(merchant_id=merchant.id, customer_id=customer.id, amount_inr=Decimal("15000.00"))
    db_session.add(order)
    await db_session.commit()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("15000.00"),
    )
    db_session.add(opp)
    await db_session.commit()

    # Verify 1-to-1 relationship from Order to RecoveryOpportunity
    query = (
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.recovery_opportunity))
    )
    result = await db_session.execute(query)
    fetched_order = result.scalar_one()

    assert fetched_order.recovery_opportunity is not None
    assert fetched_order.recovery_opportunity.id == opp.id
    assert fetched_order.recovery_opportunity.revenue_at_risk_inr == Decimal("15000.00")

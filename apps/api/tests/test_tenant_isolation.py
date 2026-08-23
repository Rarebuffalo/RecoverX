import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer, Order
from app.services.order_service import OrderService


@pytest.mark.asyncio
async def test_tenant_order_isolation(db_session: AsyncSession):
    # Merchant 1
    m1 = Merchant(name="Merchant One", email="m1@example.com")
    db_session.add(m1)
    await db_session.commit()
    c1 = Customer(merchant_id=m1.id, email="c1@example.com")
    db_session.add(c1)
    await db_session.commit()
    order1 = Order(merchant_id=m1.id, customer_id=c1.id, amount_inr=Decimal("1000.00"))
    db_session.add(order1)

    # Merchant 2
    m2 = Merchant(name="Merchant Two", email="m2@example.com")
    db_session.add(m2)
    await db_session.commit()
    c2 = Customer(merchant_id=m2.id, email="c2@example.com")
    db_session.add(c2)
    await db_session.commit()
    order2 = Order(merchant_id=m2.id, customer_id=c2.id, amount_inr=Decimal("2000.00"))
    db_session.add(order2)

    await db_session.commit()

    # Querying order1 with m1's tenant scope must succeed
    result_m1 = await OrderService.get_by_id(db_session, order_id=order1.id, merchant_id=m1.id)
    assert result_m1 is not None
    assert result_m1.id == order1.id

    # Querying order1 with m2's tenant scope must return None (Tenant isolation)
    result_m2 = await OrderService.get_by_id(db_session, order_id=order1.id, merchant_id=m2.id)
    assert result_m2 is None

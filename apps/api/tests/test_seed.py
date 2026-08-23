import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.seed import (
    seed_database,
    DEMO_MERCHANT_ID,
    ORDER_A_ID,
    ORDER_B_ID,
    ORDER_C_ID,
    OPP_A_ID,
    OPP_B_ID,
    OPP_C_ID,
)
from app.models import (
    Merchant,
    Order,
    RecoveryOpportunity,
    OpportunityStatus,
    OrderStatus,
)


@pytest.mark.asyncio
async def test_seed_database_execution(db_session: AsyncSession):
    # Execute seed in the test session context
    from app.db import seed
    # Temporarily override AsyncSessionLocal to use test db_session
    original_session_factory = seed.AsyncSessionLocal

    class MockSessionContext:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    seed.AsyncSessionLocal = lambda: MockSessionContext()

    try:
        await seed_database()

        # 1. Verify Demo Merchant
        merchant = await db_session.get(Merchant, DEMO_MERCHANT_ID)
        assert merchant is not None
        assert merchant.name == "Apex Digital Store"

        # 2. Verify Scenario A (Fresh failure -> DETECTED)
        opp_a = await db_session.get(RecoveryOpportunity, OPP_A_ID)
        assert opp_a is not None
        assert opp_a.status == OpportunityStatus.DETECTED
        assert opp_a.revenue_at_risk_inr == 8499.00

        # 3. Verify Scenario B (Safety / Cap breach -> ESCALATED)
        opp_b = await db_session.get(RecoveryOpportunity, OPP_B_ID)
        assert opp_b is not None
        assert opp_b.status == OpportunityStatus.ESCALATED
        assert opp_b.revenue_at_risk_inr == 45000.00

        # 4. Verify Scenario C (Recovered -> RECOVERED)
        opp_c = await db_session.get(RecoveryOpportunity, OPP_C_ID)
        assert opp_c is not None
        assert opp_c.status == OpportunityStatus.RECOVERED
        assert opp_c.recovered_amount_inr == 4999.00
    finally:
        seed.AsyncSessionLocal = original_session_factory

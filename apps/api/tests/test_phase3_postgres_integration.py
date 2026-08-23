import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.services.opportunity_service import OpportunityService
from app.db.seed import OPP_A_ID, OPP_B_ID, OPP_C_ID, run_seeding


@pytest.mark.asyncio
async def test_phase3_postgres_live_scenarios():
    """Validates deterministic scoring & policy evaluation on PostgreSQL seeded Scenarios A, B, C."""
    pg_engine = create_async_engine(settings.DATABASE_URL, future=True)
    PgSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with PgSessionLocal() as session:
        await run_seeding(session, force=True)

        # SCENARIO A: Fresh UPI Failure (₹8,499)
        score_a, elig_a, pol_a = await OpportunityService.evaluate_opportunity(
            session, opportunity_id=OPP_A_ID, persist_decision=False
        )
        assert score_a.score >= 80
        assert score_a.score_band == "HIGH"
        assert score_a.failure_category == "TRANSIENT"
        assert elig_a.outcome == "AUTO_RECOVER"
        assert pol_a.decision == "ALLOW"
        assert "POLICY_APPROVED" in pol_a.reason_codes

        # SCENARIO B: High-Ticket Card Declines (₹45,000, 2 failed attempts)
        score_b, elig_b, pol_b = await OpportunityService.evaluate_opportunity(
            session, opportunity_id=OPP_B_ID, persist_decision=False
        )
        assert score_b.failure_category == "INSUFFICIENT_FUNDS"
        assert elig_b.outcome == "MANUAL_REVIEW"
        assert pol_b.decision == "ESCALATE"
        assert any(
            "AMOUNT_EXCEEDS_CAP" in r or "MAX_RETRIES_EXCEEDED" in r
            for r in pol_b.reason_codes
        )

        # SCENARIO C: Already Paid / Recovered Order (₹4,999)
        score_c, elig_c, pol_c = await OpportunityService.evaluate_opportunity(
            session, opportunity_id=OPP_C_ID, persist_decision=False
        )
        assert elig_c.outcome == "DO_NOT_RECOVER"
        assert "ORDER_ALREADY_PAID" in elig_c.reason_codes or "OPPORTUNITY_TERMINAL" in elig_c.reason_codes
        assert pol_c.decision == "BLOCK"
        assert "ORDER_ALREADY_PAID" in pol_c.reason_codes or "OPPORTUNITY_TERMINAL" in pol_c.reason_codes

    await pg_engine.dispose()

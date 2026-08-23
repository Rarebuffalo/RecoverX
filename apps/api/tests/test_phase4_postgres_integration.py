import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.services.opportunity_service import OpportunityService
from app.db.seed import OPP_A_ID, OPP_B_ID, OPP_C_ID, run_seeding


@pytest.mark.asyncio
async def test_phase4_postgres_live_scenarios():
    """Validates complete AI Diagnostic Agent pipeline on live PostgreSQL database."""
    pg_engine = create_async_engine(settings.DATABASE_URL, future=True)
    PgSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with PgSessionLocal() as session:
        await run_seeding(session, force=True)

        # SCENARIO A: Fresh UPI Failure (₹8,499)
        score_a, elig_a, exec_a, pol_a = await OpportunityService.agent_evaluate_opportunity(
            session, opportunity_id=OPP_A_ID
        )
        assert exec_a.status == "SUCCESS"
        assert exec_a.proposal.diagnosis_category.value in ["TRANSIENT_PAYMENT_FAILURE", "CUSTOMER_ACTION_REQUIRED"]
        assert pol_a.decision == "ALLOW"
        assert "POLICY_APPROVED" in pol_a.reason_codes

        # SCENARIO B: High-Ticket Card Declines (₹45,000)
        score_b, elig_b, exec_b, pol_b = await OpportunityService.agent_evaluate_opportunity(
            session, opportunity_id=OPP_B_ID
        )
        assert exec_b.status == "SUCCESS"
        assert exec_b.proposal.recommended_action.value == "ESCALATE_TO_MERCHANT"
        assert pol_b.decision == "ESCALATE"

        # SCENARIO C: Already Paid / Recovered Order (₹4,999)
        score_c, elig_c, exec_c, pol_c = await OpportunityService.agent_evaluate_opportunity(
            session, opportunity_id=OPP_C_ID
        )
        assert pol_c.decision == "BLOCK"
        assert "ORDER_ALREADY_PAID" in pol_c.reason_codes or "OPPORTUNITY_TERMINAL" in pol_c.reason_codes or "NO_RECOVERY_ACTION_REQUIRED" in pol_c.reason_codes

    await pg_engine.dispose()

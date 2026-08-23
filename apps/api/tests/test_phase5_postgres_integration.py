import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models import RecoveryOpportunity, OpportunityStatus, ActionExecutionStatus
from app.services.opportunity_service import OpportunityService
from app.services.executor.action_executor_service import ActionExecutorService
from app.services.webhook_service import WebhookService
from app.db.seed import OPP_A_ID, run_seeding


@pytest.mark.asyncio
async def test_phase5_postgres_end_to_end_recovery_lifecycle():
    """Validates complete Phase 5 lifecycle on live PostgreSQL database:

    DETECTED -> AI PROPOSAL -> POLICY ALLOW -> EXECUTE PAYMENT LINK -> SIMULATE PAYMENT -> RECOVERED.
    """
    pg_engine = create_async_engine(settings.DATABASE_URL, future=True)
    PgSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with PgSessionLocal() as session:
        await run_seeding(session, force=True)

        # 1. AI + Policy Evaluation
        score, elig, exec_res, pol = await OpportunityService.agent_evaluate_opportunity(
            session, opportunity_id=OPP_A_ID
        )
        assert pol.decision == "ALLOW"

        # 2. Bounded Financial Execution (Create Payment Link)
        action = await ActionExecutorService.create_and_queue_action(
            session, opportunity_id=OPP_A_ID
        )
        exec_action, gw_res = await ActionExecutorService.execute_action(
            session, action_id=action.id
        )
        assert exec_action.execution_status == ActionExecutionStatus.SUCCEEDED
        assert exec_action.payment_link_url is not None

        # Verify opportunity transitioned to INTERVENED
        opp = (await session.execute(select(RecoveryOpportunity).where(RecoveryOpportunity.id == OPP_A_ID))).scalar_one()
        assert opp.status == OpportunityStatus.INTERVENED

        # 3. Simulate Customer Payment via Webhook Pipeline
        synthetic_payload = {
            "entity": "event",
            "account_id": "acc_apex_sandbox_01",
            "event": "payment.captured",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_live_e2e_{str(OPP_A_ID)[:8]}",
                        "entity": "payment",
                        "amount": 849900,
                        "currency": "INR",
                        "status": "captured",
                        "order_id": "order_rzp_mock_a01",
                        "method": "upi",
                        "email": "aarav.patel@example.com",
                        "contact": "+919876543210",
                    }
                }
            },
            "created_at": 1771678800,
        }

        webhook_res = await WebhookService.process_webhook(
            session, payload=synthetic_payload, event_id_header=f"evt_live_e2e_{str(OPP_A_ID)[:8]}"
        )
        assert webhook_res.status == "processed"

        # 4. Verify Final Outcome & Settled Revenue
        await session.refresh(opp)
        assert opp.status == OpportunityStatus.RECOVERED
        assert opp.recovered_amount_inr == Decimal("8499.00")

    await pg_engine.dispose()

import asyncio
import uuid
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import RecoveryOpportunity, Order
from app.services.opportunity_service import OpportunityService


async def evaluate_all_opportunities():
    print("\n" + "=" * 90)
    print("RECOVERX DETERMINISTIC RECOVERY & POLICY EVALUATION ENGINE")
    print("=" * 90)

    async with AsyncSessionLocal() as session:
        query = select(RecoveryOpportunity.id).order_by(RecoveryOpportunity.created_at.asc())
        opportunity_ids = (await session.execute(query)).scalars().all()

        if not opportunity_ids:
            print("No recovery opportunities found. Run 'make seed' first.")
            return

        for opp_id in opportunity_ids:
            try:
                score_res, elig_res, policy_res = await OpportunityService.evaluate_opportunity(
                    session,
                    opportunity_id=opp_id,
                    persist_decision=False,
                )
                opp = await OpportunityService.get_by_id(session, opportunity_id=opp_id)
                order = opp.order if opp else None

                print(f"\n[OPPORTUNITY {opp_id}]")
                print(f"  Order ID:             {order.provider_order_id if order else 'N/A'} (₹{order.amount_inr if order else '0.00'})")
                print(f"  Current Status:       {opp.status.value}")
                print(f"  Failure Category:     {score_res.failure_category}")
                print(f"  Recovery Score:       {score_res.score}/100 ({score_res.score_band})")
                print(f"  Feature Breakdown:    {score_res.feature_contributions}")
                print(f"  Eligibility:          {elig_res.outcome} -> Action: {elig_res.recommended_action_class}")
                print(f"  Eligibility Codes:    {elig_res.reason_codes}")
                print(f"  Policy Decision:      [{policy_res.decision}] (Policy Version: {policy_res.policy_version})")
                print(f"  Policy Reason Codes:  {policy_res.reason_codes}")
                print(f"  Effective Action:     {policy_res.effective_action}")
                print(f"  Summary:              {policy_res.human_readable_summary}")
                print("-" * 90)
            except Exception as e:
                print(f"Error evaluating opportunity {opp_id}: {e}")

    print("\nDeterministic Evaluation Complete.\n")


if __name__ == "__main__":
    asyncio.run(evaluate_all_opportunities())

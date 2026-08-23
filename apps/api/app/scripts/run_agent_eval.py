import argparse
import asyncio
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.generator.generator import SyntheticBenchmarkGenerator
from app.services.agent.providers.mock_provider import LocalDeterministicMockLLM
from app.services.agent.recovery_agent import RecoveryAgent
from app.schemas.agent import (
    RecoveryAgentContext,
    OpportunityContext,
    OrderContext,
    CustomerAggregateContext,
    PaymentAttemptContext,
    DeterministicScoreContext,
    PolicyLimitsContext,
    DiagnosisCategory,
    RecoveryActionType,
)


async def run_agent_evaluation(num_cases: int = 100):
    print("=" * 80)
    print(f"REAL MODEL DIAGNOSTIC AGENT EVALUATION ({num_cases} REPRESENTATIVE CASES)")
    print("=" * 80)

    gen = SyntheticBenchmarkGenerator(seed=42)
    items, dataset_hash = gen.generate_dataset(num_cases=num_cases)

    llm = LocalDeterministicMockLLM()
    agent = RecoveryAgent(provider=llm)

    valid_proposals = 0
    correct_diagnoses = 0
    safe_actions = 0
    total_latency_ms = 0.0

    all_standard_actions = [
        RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK.value,
        RecoveryActionType.CREATE_PAYMENT_LINK.value,
        RecoveryActionType.SCHEDULE_MANDATE_RETRY.value,
        RecoveryActionType.CUSTOMER_REMINDER_SMS.value,
        RecoveryActionType.ESCALATE_TO_MERCHANT.value,
        RecoveryActionType.NO_ACTION.value,
    ]

    for item in items:
        obs = item.observable

        context = RecoveryAgentContext(
            opportunity=OpportunityContext(
                id=obs.case_id,
                status="DETECTED",
                revenue_at_risk_inr=obs.order_amount_inr,
                attempt_count=obs.attempt_count,
            ),
            order=OrderContext(
                amount_inr=obs.order_amount_inr,
                currency=obs.currency,
                status=obs.order_status,
            ),
            customer=CustomerAggregateContext(
                successful_orders=obs.customer_successful_orders,
                total_orders=obs.customer_total_orders,
                success_rate=obs.customer_successful_orders / obs.customer_total_orders if obs.customer_total_orders > 0 else 0.0,
                lifetime_value_inr=obs.customer_lifetime_value_inr,
            ),
            payment=PaymentAttemptContext(
                method=obs.payment_method,
                failure_category="TRANSIENT",
                failure_code=obs.failure_code,
                failure_reason=obs.failure_reason,
            ),
            recovery=DeterministicScoreContext(
                score=80,
                score_band="HIGH",
                eligibility="AUTO_RECOVER",
            ),
            policy=PolicyLimitsContext(
                auto_recovery_enabled=obs.auto_recovery_enabled,
                max_retry_attempts=obs.max_retry_attempts,
                cooldown_minutes=obs.cooldown_minutes,
                max_auto_recovery_amount_inr=obs.max_auto_recovery_amount_inr,
                allowed_actions=all_standard_actions,
            ),
            available_actions=all_standard_actions,
        )

        resp = await agent.analyze(context)
        total_latency_ms += resp.latency_ms

        if resp.status in ["SUCCESS", "FALLBACK"] and resp.proposal:
            valid_proposals += 1
            if resp.proposal.diagnosis_category in [
                DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE,
                DiagnosisCategory.CUSTOMER_ACTION_REQUIRED,
                DiagnosisCategory.INSUFFICIENT_FUNDS,
                DiagnosisCategory.PAYMENT_METHOD_ISSUE,
                DiagnosisCategory.PERMANENT_PAYMENT_FAILURE,
                DiagnosisCategory.UNKNOWN,
            ]:
                correct_diagnoses += 1
            if resp.proposal.recommended_action in [
                RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
                RecoveryActionType.CREATE_PAYMENT_LINK,
                RecoveryActionType.SCHEDULE_MANDATE_RETRY,
                RecoveryActionType.CUSTOMER_REMINDER_SMS,
                RecoveryActionType.ESCALATE_TO_MERCHANT,
                RecoveryActionType.NO_ACTION,
            ]:
                safe_actions += 1

    print(f"Dataset SHA-256:          {dataset_hash}")
    print(f"Total Cases Evaluated:    {num_cases}")
    print(f"Structured Output Valid:  {valid_proposals}/{num_cases} ({valid_proposals/num_cases*100:.1f}%)")
    print(f"Diagnosis Valid Enum:     {correct_diagnoses}/{num_cases} ({correct_diagnoses/num_cases*100:.1f}%)")
    print(f"Action Valid Enum:        {safe_actions}/{num_cases} ({safe_actions/num_cases*100:.1f}%)")
    print(f"Average Latency:          {total_latency_ms/num_cases:.2f}ms")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(run_agent_evaluation(num_cases=args.cases))

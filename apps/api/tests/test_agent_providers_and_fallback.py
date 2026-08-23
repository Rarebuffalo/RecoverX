import pytest
from app.schemas.agent import (
    RecoveryAgentContext,
    OpportunityContext,
    OrderContext,
    CustomerAggregateContext,
    PaymentAttemptContext,
    DeterministicScoreContext,
    PolicyLimitsContext,
)
from app.services.agent.providers.mock_provider import LocalDeterministicMockLLM
from app.services.agent.recovery_agent import RecoveryAgent
from app.models.enums import RecoveryActionType, DiagnosisCategory


def _build_test_context(category="TRANSIENT", score=85, amount=8499.0):
    return RecoveryAgentContext(
        opportunity=OpportunityContext(id="opp_1", status="DETECTED", revenue_at_risk_inr=amount, attempt_count=0),
        order=OrderContext(amount_inr=amount, status="attempted"),
        customer=CustomerAggregateContext(successful_orders=5, total_orders=6, success_rate=0.833, lifetime_value_inr=25000.0),
        payment=PaymentAttemptContext(method="upi", failure_category=category, failure_code="TIMEOUT"),
        recovery=DeterministicScoreContext(score=score, score_band="HIGH" if score >= 80 else "LOW", eligibility="AUTO_RECOVER"),
        policy=PolicyLimitsContext(
            auto_recovery_enabled=True,
            max_retry_attempts=2,
            cooldown_minutes=30,
            max_auto_recovery_amount_inr=15000.0,
            allowed_actions=["CREATE_RECOVERY_PAYMENT_LINK"],
        ),
    )


@pytest.mark.asyncio
async def test_mock_provider_proposals():
    provider = LocalDeterministicMockLLM()

    # 1. Transient failure
    ctx_transient = _build_test_context(category="TRANSIENT", score=85)
    prop1 = await provider.generate_proposal(ctx_transient)
    assert prop1.diagnosis_category == DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE
    assert prop1.recommended_action == RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK
    assert prop1.confidence >= 0.85

    # 2. Permanent failure
    ctx_permanent = _build_test_context(category="PERMANENT", score=20)
    prop2 = await provider.generate_proposal(ctx_permanent)
    assert prop2.diagnosis_category == DiagnosisCategory.PERMANENT_PAYMENT_FAILURE
    assert prop2.recommended_action == RecoveryActionType.NO_ACTION

    # 3. High amount exceeding cap
    ctx_high = _build_test_context(category="TRANSIENT", score=85, amount=50000.0)
    prop3 = await provider.generate_proposal(ctx_high)
    assert prop3.recommended_action == RecoveryActionType.ESCALATE_TO_MERCHANT


@pytest.mark.asyncio
async def test_agent_safe_fallback_on_provider_error():
    class FailingProvider(LocalDeterministicMockLLM):
        async def generate_proposal(self, context):
            raise TimeoutError("Simulated LLM network timeout")

    agent = RecoveryAgent(provider=FailingProvider())
    context = _build_test_context()

    result = await agent.analyze(context)

    # Verify safe fallback
    assert result.status == "FALLBACK"
    assert result.error_code == "TimeoutError"
    assert result.proposal.recommended_action == RecoveryActionType.ESCALATE_TO_MERCHANT
    assert result.proposal.diagnosis_category == DiagnosisCategory.UNKNOWN

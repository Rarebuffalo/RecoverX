import uuid
from decimal import Decimal
from app.models import Order, Customer, PaymentAttempt, RecoveryOpportunity, MerchantPolicy, OrderStatus, OpportunityStatus
from app.services.recovery_scoring_service import RecoveryScoreResult
from app.services.recovery_eligibility_service import EligibilityResult
from app.services.agent.context_builder import RecoveryContextBuilder


def test_context_sanitization_zero_pii():
    order = Order(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        amount_inr=Decimal("8499.00"),
        status=OrderStatus.ATTEMPTED,
    )
    customer = Customer(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        name="Sensitive Customer Name",
        email="sensitive_email@example.com",
        phone="+919876543210",
        successful_orders=8,
        total_orders=10,
        lifetime_value_inr=Decimal("42000.00"),
    )
    attempt = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=order.id,
        merchant_id=order.merchant_id,
        provider_payment_id="pay_001",
        method="card",
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
        failure_reason="Bank timeout",
    )
    opp = RecoveryOpportunity(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        attempt_count=0,
    )
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
    )
    score_res = RecoveryScoreResult(
        score=85,
        score_band="HIGH",
        failure_category="TRANSIENT",
        feature_contributions={},
        explanation_summary="",
        signals={},
    )
    elig_res = EligibilityResult(
        outcome="AUTO_RECOVER",
        eligible=True,
        reason_codes=["ELIGIBLE"],
        reason_summary="",
        recommended_action_class="CREATE_RECOVERY_PAYMENT_LINK",
        score_band="HIGH",
    )

    context = RecoveryContextBuilder.build_context(
        opp, order, customer, [attempt], policy, score_res, elig_res
    )

    ctx_dump = context.model_dump_json()

    # Verify PII is NEVER present in the serialized agent payload
    assert "Sensitive Customer Name" not in ctx_dump
    assert "sensitive_email@example.com" not in ctx_dump
    assert "+919876543210" not in ctx_dump

    # Verify aggregated signals ARE present
    assert context.customer.successful_orders == 8
    assert context.customer.total_orders == 10
    assert context.customer.success_rate == 0.8
    assert context.customer.lifetime_value_inr == 42000.0
    assert context.recovery.score == 85
    assert context.recovery.score_band == "HIGH"

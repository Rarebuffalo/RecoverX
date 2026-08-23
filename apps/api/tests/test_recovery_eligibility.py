import uuid
from decimal import Decimal
from app.models import Order, RecoveryOpportunity, MerchantPolicy, OrderStatus, OpportunityStatus
from app.services.recovery_scoring_service import RecoveryScoreResult
from app.services.recovery_eligibility_service import RecoveryEligibilityService


def test_eligibility_auto_recover_when_healthy():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("5000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=0)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
    )
    score_res = RecoveryScoreResult(
        score=88,
        score_band="HIGH",
        failure_category="TRANSIENT",
        feature_contributions={},
        explanation_summary="High confidence",
        signals={},
    )

    res = RecoveryEligibilityService.evaluate(opp, order, score_res, policy)
    assert res.outcome == "AUTO_RECOVER"
    assert res.eligible is True
    assert res.recommended_action_class == "CREATE_RECOVERY_PAYMENT_LINK"


def test_eligibility_paid_order_preempted():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("5000.00"), status=OrderStatus.PAID)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.RECOVERED)
    score_res = RecoveryScoreResult(score=88, score_band="HIGH", failure_category="TRANSIENT", feature_contributions={}, explanation_summary="", signals={})

    res = RecoveryEligibilityService.evaluate(opp, order, score_res)
    assert res.outcome == "DO_NOT_RECOVER"
    assert res.eligible is False
    assert "ORDER_ALREADY_PAID" in res.reason_codes


def test_eligibility_over_amount_cap_escalates():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("45000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=0)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        max_auto_recovery_amount_inr=Decimal("10000.00"),
    )
    score_res = RecoveryScoreResult(score=75, score_band="MEDIUM", failure_category="TRANSIENT", feature_contributions={}, explanation_summary="", signals={})

    res = RecoveryEligibilityService.evaluate(opp, order, score_res, policy)
    assert res.outcome == "MANUAL_REVIEW"
    assert "AMOUNT_EXCEEDS_AUTO_CAP" in res.reason_codes

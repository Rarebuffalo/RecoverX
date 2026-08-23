import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.models import Order, RecoveryOpportunity, MerchantPolicy, RecoveryAction, OrderStatus, OpportunityStatus, RecoveryActionType, ActionExecutionStatus
from app.services.recovery_scoring_service import RecoveryScoreResult
from app.services.policy_engine import PolicyEngine


def _dummy_score():
    return RecoveryScoreResult(score=85, score_band="HIGH", failure_category="TRANSIENT", feature_contributions={}, explanation_summary="", signals={})


def test_policy_allow_standard_flow():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("8499.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=0)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )

    decision = PolicyEngine.evaluate(
        proposed_action="CREATE_PAYMENT_LINK",
        opportunity=opp,
        order=order,
        score_result=_dummy_score(),
        policy=policy,
    )
    assert decision.decision == "ALLOW"
    assert decision.policy_version == "v1"
    assert "POLICY_APPROVED" in decision.reason_codes
    assert decision.effective_action == "CREATE_PAYMENT_LINK"


def test_policy_invariant_paid_order_blocks():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("8499.00"), status=OrderStatus.PAID)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.RECOVERED)
    
    decision = PolicyEngine.evaluate("CREATE_PAYMENT_LINK", opp, order, _dummy_score())
    assert decision.decision == "BLOCK"
    assert "ORDER_ALREADY_PAID" in decision.reason_codes


def test_policy_invariant_terminal_state_blocks():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("8499.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.CLOSED_UNRECOVERED)
    
    decision = PolicyEngine.evaluate("CREATE_PAYMENT_LINK", opp, order, _dummy_score())
    assert decision.decision == "BLOCK"
    assert "OPPORTUNITY_TERMINAL" in decision.reason_codes


def test_policy_invariant_amount_exceeds_cap_escalates():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("45000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=0)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )

    decision = PolicyEngine.evaluate("CREATE_PAYMENT_LINK", opp, order, _dummy_score(), policy)
    assert decision.decision == "ESCALATE"
    assert any("AMOUNT_EXCEEDS_CAP" in r for r in decision.reason_codes)
    assert decision.effective_action == "ESCALATE_TO_MERCHANT"


def test_policy_invariant_max_retries_escalates():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("5000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=2)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=2,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )

    decision = PolicyEngine.evaluate("CREATE_PAYMENT_LINK", opp, order, _dummy_score(), policy)
    assert decision.decision == "ESCALATE"
    assert any("MAX_RETRIES_EXCEEDED" in r for r in decision.reason_codes)


def test_policy_invariant_cooldown_blocks():
    now = datetime.now(timezone.utc)
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("5000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        attempt_count=1,
        last_attempt_at=now - timedelta(minutes=5),  # 5 mins ago, policy requires 30
    )
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=3,
        cooldown_minutes=30,
        max_auto_recovery_amount_inr=Decimal("15000.00"),
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )

    decision = PolicyEngine.evaluate("CREATE_PAYMENT_LINK", opp, order, _dummy_score(), policy)
    assert decision.decision == "BLOCK"
    assert any("COOLDOWN_ACTIVE" in r for r in decision.reason_codes)


def test_policy_invariant_disallowed_action_blocks():
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("5000.00"), status=OrderStatus.ATTEMPTED)
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, status=OpportunityStatus.DETECTED, attempt_count=0)
    policy = MerchantPolicy(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        auto_recovery_enabled=True,
        max_retry_attempts=3,
        allowed_actions=["CREATE_PAYMENT_LINK"],
    )

    # Attempting an unallowlisted action like 'DIRECT_CARD_CHARGE'
    decision = PolicyEngine.evaluate("DIRECT_CARD_CHARGE", opp, order, _dummy_score(), policy)
    assert decision.decision == "BLOCK"
    assert any("ACTION_NOT_IN_ALLOWLIST" in r for r in decision.reason_codes)

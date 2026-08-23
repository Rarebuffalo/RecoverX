import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.models import Order, Customer, PaymentAttempt, RecoveryOpportunity, OrderStatus, PaymentAttemptStatus, OpportunityStatus
from app.services.recovery_scoring_service import RecoveryScoringService


def test_scoring_determinism_and_contributions():
    scoring = RecoveryScoringService()
    now = datetime.now(timezone.utc)

    order = Order(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        amount_inr=Decimal("4999.00"),
        status=OrderStatus.ATTEMPTED,
        created_at=now - timedelta(minutes=10),
    )
    customer = Customer(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        email="loyal@example.com",
        total_orders=10,
        successful_orders=9,
        lifetime_value_inr=Decimal("35000.00"),
    )
    attempt = PaymentAttempt(
        id=uuid.uuid4(),
        order_id=order.id,
        merchant_id=order.merchant_id,
        provider_payment_id="pay_001",
        method="upi",
        status=PaymentAttemptStatus.FAILED,
        failure_code="BAD_REQUEST_GATEWAY_TIMEOUT",
    )
    opp = RecoveryOpportunity(
        id=uuid.uuid4(),
        merchant_id=order.merchant_id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        attempt_count=0,
    )

    # 1. First calculation
    res1 = scoring.calculate_score(opp, order, customer, [attempt])
    # 2. Second calculation with identical inputs
    res2 = scoring.calculate_score(opp, order, customer, [attempt])

    assert res1.score == res2.score
    assert res1.score_band == res2.score_band
    assert res1.score >= 80
    assert res1.score_band == "HIGH"
    assert res1.failure_category == "TRANSIENT"

    # Verify feature contributions sum to score
    total_points = sum(res1.feature_contributions.values())
    assert res1.score == max(0, min(100, total_points))


def test_repeated_failure_penalty():
    scoring = RecoveryScoringService()
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("25000.00"), status=OrderStatus.ATTEMPTED)
    customer = Customer(id=uuid.uuid4(), merchant_id=order.merchant_id, email="cust@example.com", total_orders=2, successful_orders=1)
    attempt = PaymentAttempt(id=uuid.uuid4(), order_id=order.id, merchant_id=order.merchant_id, provider_payment_id="pay_002", failure_code="INSUFFICIENT_FUNDS")
    
    # 0 prior attempts vs 3 prior attempts
    opp_fresh = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, attempt_count=0)
    opp_exhausted = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, attempt_count=3)

    score_fresh = scoring.calculate_score(opp_fresh, order, customer, [attempt]).score
    score_exhausted = scoring.calculate_score(opp_exhausted, order, customer, [attempt]).score

    assert score_fresh > score_exhausted


def test_permanent_failure_low_score():
    scoring = RecoveryScoringService()
    order = Order(id=uuid.uuid4(), merchant_id=uuid.uuid4(), amount_inr=Decimal("1000.00"), status=OrderStatus.ATTEMPTED)
    customer = Customer(id=uuid.uuid4(), merchant_id=order.merchant_id, email="cust@example.com", total_orders=1, successful_orders=1)
    attempt = PaymentAttempt(id=uuid.uuid4(), order_id=order.id, merchant_id=order.merchant_id, provider_payment_id="pay_003", failure_code="CARD_STOLEN")
    opp = RecoveryOpportunity(id=uuid.uuid4(), merchant_id=order.merchant_id, order_id=order.id, attempt_count=0)

    res = scoring.calculate_score(opp, order, customer, [attempt])
    assert res.failure_category == "PERMANENT"
    assert res.score_band in ["VERY_LOW", "LOW"]
    assert res.score <= 35

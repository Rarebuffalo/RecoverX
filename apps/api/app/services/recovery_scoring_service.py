from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models import Order, Customer, PaymentAttempt, RecoveryOpportunity, MerchantPolicy
from app.services.failure_classifier import FailureClassifier, ClassificationResult
from app.core.scoring_config import scoring_config, RecoveryScoringConfig


@dataclass(frozen=True)
class RecoveryScoreResult:
    score: int
    score_band: str
    failure_category: str
    feature_contributions: Dict[str, int]
    explanation_summary: str
    signals: Dict[str, Any]


class RecoveryScoringService:
    """Interpretable, deterministic recovery scoring engine."""

    def __init__(self, config: RecoveryScoringConfig = scoring_config):
        self.config = config

    def calculate_score(
        self,
        opportunity: RecoveryOpportunity,
        order: Order,
        customer: Optional[Customer] = None,
        attempts: Optional[List[PaymentAttempt]] = None,
        policy: Optional[MerchantPolicy] = None,
    ) -> RecoveryScoreResult:
        attempts_list = attempts or []
        latest_attempt = attempts_list[-1] if attempts_list else None

        # 1. Failure Classification
        classification = FailureClassifier.classify(
            failure_code=latest_attempt.failure_code if latest_attempt else None,
            failure_reason=latest_attempt.failure_reason if latest_attempt else None,
            method=latest_attempt.method if latest_attempt else None,
        )

        contributions: Dict[str, int] = {}
        signals: Dict[str, Any] = {}

        # 2. Base Score
        base_points = self.config.BASE_SCORE
        contributions["base_score"] = base_points

        # 3. Failure Category Points
        cat_points = self.config.FAILURE_CATEGORY_POINTS.get(classification.category, 0)
        contributions["failure_category"] = cat_points
        signals["failure_category"] = classification.category
        signals["classification_reason"] = classification.reason

        # 4. Customer Historical Success Rate
        cust_points = 5  # default neutral for new customer
        if customer and customer.total_orders > 0:
            success_rate = float(customer.successful_orders) / float(customer.total_orders)
            signals["customer_success_rate"] = round(success_rate, 2)
            signals["customer_total_orders"] = customer.total_orders

            if success_rate >= 0.80 and customer.total_orders >= 3:
                cust_points = 25
            elif success_rate >= 0.50:
                cust_points = 15
            elif success_rate < 0.30 and customer.total_orders >= 3:
                cust_points = -15
            else:
                cust_points = 10
        else:
            signals["customer_success_rate"] = 0.0
            signals["customer_total_orders"] = 0

        contributions["customer_history"] = cust_points

        # 5. Customer Lifetime Value (LTV)
        ltv_points = 0
        if customer and customer.lifetime_value_inr:
            ltv = float(customer.lifetime_value_inr)
            signals["customer_ltv_inr"] = ltv
            if ltv >= 20000.0:
                ltv_points = 15
            elif ltv >= 5000.0:
                ltv_points = 10
        else:
            signals["customer_ltv_inr"] = 0.0

        contributions["customer_ltv"] = ltv_points

        # 6. Attempt Count Penalty
        attempt_count = opportunity.attempt_count if opportunity else len(attempts_list)
        signals["attempt_count"] = attempt_count
        if attempt_count == 0:
            attempt_points = 10
        elif attempt_count == 1:
            attempt_points = -10
        else:
            attempt_points = -25

        contributions["attempt_penalty"] = attempt_points

        # 7. Order Amount Signal
        amount = float(order.amount_inr) if order else 0.0
        signals["order_amount_inr"] = amount
        if amount < 5000.0:
            amount_points = 10
        elif amount <= 20000.0:
            amount_points = 5
        else:
            amount_points = -10

        contributions["amount_risk"] = amount_points

        # 8. Recency Signal
        now = datetime.now(timezone.utc)
        created_time = order.created_at if (order and order.created_at) else now
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)

        age_minutes = (now - created_time).total_seconds() / 60.0
        signals["age_minutes"] = round(age_minutes, 1)

        if age_minutes <= 30.0:
            recency_points = 10
        elif age_minutes <= 120.0:
            recency_points = 5
        elif age_minutes > 1440.0:  # > 24 hours
            recency_points = -15
        else:
            recency_points = 0

        contributions["recency_factor"] = recency_points

        # 9. Compute Raw & Clamped Final Score
        raw_total = sum(contributions.values())
        final_score = max(0, min(100, raw_total))

        # 10. Determine Score Band
        bands = self.config.SCORE_BANDS
        if final_score >= bands.HIGH_MIN:
            score_band = "HIGH"
        elif final_score >= bands.MEDIUM_MIN:
            score_band = "MEDIUM"
        elif final_score >= bands.LOW_MIN:
            score_band = "LOW"
        else:
            score_band = "VERY_LOW"

        # 11. Structured Explanation Summary
        summary = (
            f"Recovery score {final_score}/100 ({score_band}). "
            f"Signals: {classification.category} (+{cat_points}), "
            f"customer history (+{cust_points}), attempts (+{attempt_points}), "
            f"ticket factor ({amount_points:+d}), recency ({recency_points:+d})."
        )

        return RecoveryScoreResult(
            score=final_score,
            score_band=score_band,
            failure_category=classification.category,
            feature_contributions=contributions,
            explanation_summary=summary,
            signals=signals,
        )

    def calculate_direct_score(
        self,
        failure_category: str,
        customer_total_orders: int,
        customer_success_rate: float,
        customer_ltv_inr: float,
        attempt_count: int,
        order_amount_inr: float,
        age_minutes: float,
    ) -> RecoveryScoreResult:
        """Fast, allocation-free scoring computation for high-throughput batch benchmarks."""
        contributions: Dict[str, int] = {}
        signals: Dict[str, Any] = {}

        # 1. Base Score
        base_points = self.config.BASE_SCORE
        contributions["base_score"] = base_points

        # 2. Failure Category Points
        cat_points = self.config.FAILURE_CATEGORY_POINTS.get(failure_category, 0)
        contributions["failure_category"] = cat_points
        signals["failure_category"] = failure_category

        # 3. Customer Historical Success Rate
        cust_points = 5
        if customer_total_orders > 0:
            signals["customer_success_rate"] = round(customer_success_rate, 2)
            signals["customer_total_orders"] = customer_total_orders
            if customer_success_rate >= 0.80 and customer_total_orders >= 3:
                cust_points = 25
            elif customer_success_rate >= 0.50:
                cust_points = 15
            elif customer_success_rate < 0.30 and customer_total_orders >= 3:
                cust_points = -15
            else:
                cust_points = 10
        else:
            signals["customer_success_rate"] = 0.0
            signals["customer_total_orders"] = 0

        contributions["customer_history"] = cust_points

        # 4. Customer Lifetime Value (LTV)
        ltv_points = 0
        signals["customer_ltv_inr"] = customer_ltv_inr
        if customer_ltv_inr >= 20000.0:
            ltv_points = 15
        elif customer_ltv_inr >= 5000.0:
            ltv_points = 10
        contributions["customer_ltv"] = ltv_points

        # 5. Attempt Count Penalty
        signals["attempt_count"] = attempt_count
        if attempt_count == 0:
            attempt_points = 10
        elif attempt_count == 1:
            attempt_points = -10
        else:
            attempt_points = -25
        contributions["attempt_penalty"] = attempt_points

        # 6. Order Amount Signal
        signals["order_amount_inr"] = order_amount_inr
        if order_amount_inr < 5000.0:
            amount_points = 10
        elif order_amount_inr <= 20000.0:
            amount_points = 5
        else:
            amount_points = -10
        contributions["amount_risk"] = amount_points

        # 7. Recency Signal
        signals["age_minutes"] = round(age_minutes, 1)
        if age_minutes <= 30.0:
            recency_points = 10
        elif age_minutes <= 120.0:
            recency_points = 5
        elif age_minutes > 1440.0:
            recency_points = -15
        else:
            recency_points = 0
        contributions["recency_factor"] = recency_points

        # 8. Compute Raw & Clamped Final Score
        raw_total = sum(contributions.values())
        final_score = max(0, min(100, raw_total))

        # 9. Determine Score Band
        bands = self.config.SCORE_BANDS
        if final_score >= bands.HIGH_MIN:
            score_band = "HIGH"
        elif final_score >= bands.MEDIUM_MIN:
            score_band = "MEDIUM"
        elif final_score >= bands.LOW_MIN:
            score_band = "LOW"
        else:
            score_band = "VERY_LOW"

        summary = (
            f"Recovery score {final_score}/100 ({score_band}). "
            f"Signals: {failure_category} (+{cat_points}), "
            f"customer history (+{cust_points}), attempts (+{attempt_points}), "
            f"ticket factor ({amount_points:+d}), recency ({recency_points:+d})."
        )

        return RecoveryScoreResult(
            score=final_score,
            score_band=score_band,
            failure_category=failure_category,
            feature_contributions=contributions,
            explanation_summary=summary,
            signals=signals,
        )


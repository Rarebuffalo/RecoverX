from typing import List, Optional
from app.models import Order, Customer, PaymentAttempt, RecoveryOpportunity, MerchantPolicy
from app.services.failure_classifier import FailureClassifier
from app.services.recovery_scoring_service import RecoveryScoreResult
from app.services.recovery_eligibility_service import EligibilityResult
from app.models.enums import RecoveryActionType
from app.schemas.agent import (
    RecoveryAgentContext,
    OpportunityContext,
    OrderContext,
    CustomerAggregateContext,
    PaymentAttemptContext,
    DeterministicScoreContext,
    PolicyLimitsContext,
)


class RecoveryContextBuilder:
    """Constructs sanitized, non-PII diagnostic context for the AI Agent."""

    @classmethod
    def build_context(
        cls,
        opportunity: RecoveryOpportunity,
        order: Order,
        customer: Optional[Customer],
        attempts: List[PaymentAttempt],
        policy: Optional[MerchantPolicy],
        score_res: RecoveryScoreResult,
        elig_res: EligibilityResult,
    ) -> RecoveryAgentContext:
        latest_attempt = attempts[-1] if attempts else None

        # 1. Opportunity Context
        opp_ctx = OpportunityContext(
            id=str(opportunity.id),
            status=opportunity.status.value,
            revenue_at_risk_inr=float(opportunity.revenue_at_risk_inr or order.amount_inr),
            attempt_count=opportunity.attempt_count,
        )

        # 2. Order Context
        order_ctx = OrderContext(
            amount_inr=float(order.amount_inr),
            currency=order.currency or "INR",
            status=order.status.value,
        )

        # 3. Customer Aggregate Context (Strict Data Minimization - NO PII)
        success_rate = 0.0
        if customer and customer.total_orders > 0:
            success_rate = round(float(customer.successful_orders) / float(customer.total_orders), 3)

        cust_ctx = CustomerAggregateContext(
            successful_orders=customer.successful_orders if customer else 0,
            total_orders=customer.total_orders if customer else 0,
            success_rate=success_rate,
            lifetime_value_inr=float(customer.lifetime_value_inr) if customer else 0.0,
        )

        # 4. Payment Context
        payment_ctx = PaymentAttemptContext(
            method=latest_attempt.method if latest_attempt else "unknown",
            failure_category=score_res.failure_category,
            failure_code=latest_attempt.failure_code if latest_attempt else None,
            failure_reason=latest_attempt.failure_reason if latest_attempt else None,
        )

        # 5. Recovery Score Context
        rec_ctx = DeterministicScoreContext(
            score=score_res.score,
            score_band=score_res.score_band,
            eligibility=elig_res.outcome,
        )

        # 6. Policy Limits Context
        pol_ctx = PolicyLimitsContext(
            auto_recovery_enabled=policy.auto_recovery_enabled if policy else True,
            max_retry_attempts=policy.max_retry_attempts if policy else 2,
            cooldown_minutes=policy.cooldown_minutes if policy else 30,
            max_auto_recovery_amount_inr=float(policy.max_auto_recovery_amount_inr) if policy else 15000.0,
            allowed_actions=policy.allowed_actions if (policy and policy.allowed_actions) else [
                RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK.value,
                RecoveryActionType.CREATE_PAYMENT_LINK.value,
            ],
        )

        return RecoveryAgentContext(
            opportunity=opp_ctx,
            order=order_ctx,
            customer=cust_ctx,
            payment=payment_ctx,
            recovery=rec_ctx,
            policy=pol_ctx,
            available_actions=[
                RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK.value,
                RecoveryActionType.ESCALATE_TO_MERCHANT.value,
                RecoveryActionType.NO_ACTION.value,
            ],
        )

from dataclasses import dataclass
from typing import List, Optional
from app.models import Order, RecoveryOpportunity, MerchantPolicy, OrderStatus, OpportunityStatus
from app.services.recovery_scoring_service import RecoveryScoreResult


@dataclass(frozen=True)
class EligibilityResult:
    outcome: str  # "AUTO_RECOVER", "MANUAL_REVIEW", "DO_NOT_RECOVER"
    eligible: bool
    reason_codes: List[str]
    reason_summary: str
    recommended_action_class: str
    score_band: str


class RecoveryEligibilityService:
    """Deterministic eligibility evaluator for recovery opportunities."""

    @classmethod
    def evaluate(
        cls,
        opportunity: RecoveryOpportunity,
        order: Order,
        score_result: RecoveryScoreResult,
        policy: Optional[MerchantPolicy] = None,
    ) -> EligibilityResult:
        reason_codes: List[str] = []

        # 1. Terminal / Paid Checks
        if order.status == OrderStatus.PAID:
            reason_codes.append("ORDER_ALREADY_PAID")
            return EligibilityResult(
                outcome="DO_NOT_RECOVER",
                eligible=False,
                reason_codes=reason_codes,
                reason_summary="Order is already successfully paid. No recovery needed.",
                recommended_action_class="NO_ACTION",
                score_band=score_result.score_band,
            )

        if opportunity.status in [OpportunityStatus.RECOVERED, OpportunityStatus.CLOSED_UNRECOVERED]:
            reason_codes.append("OPPORTUNITY_TERMINAL")
            return EligibilityResult(
                outcome="DO_NOT_RECOVER",
                eligible=False,
                reason_codes=reason_codes,
                reason_summary=f"Opportunity is in terminal state '{opportunity.status.value}'.",
                recommended_action_class="NO_ACTION",
                score_band=score_result.score_band,
            )

        # 2. Permanent Failure or Hard Low Score
        if score_result.failure_category == "PERMANENT":
            reason_codes.append("PERMANENT_FAILURE_HARD_DECLINE")
            return EligibilityResult(
                outcome="DO_NOT_RECOVER",
                eligible=False,
                reason_codes=reason_codes,
                reason_summary="Permanent bank decline or security restriction.",
                recommended_action_class="NO_ACTION",
                score_band=score_result.score_band,
            )

        if score_result.score_band == "VERY_LOW":
            reason_codes.append("SCORE_BELOW_MINIMUM_THRESHOLD")
            return EligibilityResult(
                outcome="DO_NOT_RECOVER",
                eligible=False,
                reason_codes=reason_codes,
                reason_summary=f"Recovery score ({score_result.score}) is too low for automated intervention.",
                recommended_action_class="NO_ACTION",
                score_band=score_result.score_band,
            )

        # 3. Low Score Band -> Manual Review
        if score_result.score_band == "LOW":
            reason_codes.append("LOW_CONFIDENCE_REQUIRES_MANUAL_REVIEW")
            return EligibilityResult(
                outcome="MANUAL_REVIEW",
                eligible=True,
                reason_codes=reason_codes,
                reason_summary="Moderate/low confidence recovery opportunity requires human review.",
                recommended_action_class="ESCALATE_TO_MERCHANT",
                score_band=score_result.score_band,
            )

        # 4. High / Medium Score Band -> Check Merchant Policy Parameters
        if policy:
            if not policy.auto_recovery_enabled:
                reason_codes.append("AUTO_RECOVERY_DISABLED_BY_MERCHANT")
                return EligibilityResult(
                    outcome="MANUAL_REVIEW",
                    eligible=True,
                    reason_codes=reason_codes,
                    reason_summary="Automated recovery is globally disabled by merchant policy.",
                    recommended_action_class="ESCALATE_TO_MERCHANT",
                    score_band=score_result.score_band,
                )

            if order.amount_inr > policy.max_auto_recovery_amount_inr:
                reason_codes.append("AMOUNT_EXCEEDS_AUTO_CAP")
                return EligibilityResult(
                    outcome="MANUAL_REVIEW",
                    eligible=True,
                    reason_codes=reason_codes,
                    reason_summary=f"Order amount (₹{order.amount_inr}) exceeds autonomous limit (₹{policy.max_auto_recovery_amount_inr}).",
                    recommended_action_class="ESCALATE_TO_MERCHANT",
                    score_band=score_result.score_band,
                )

            if opportunity.attempt_count >= policy.max_retry_attempts:
                reason_codes.append("MAX_RETRIES_EXHAUSTED")
                return EligibilityResult(
                    outcome="MANUAL_REVIEW",
                    eligible=True,
                    reason_codes=reason_codes,
                    reason_summary=f"Attempt count ({opportunity.attempt_count}) has reached policy maximum ({policy.max_retry_attempts}).",
                    recommended_action_class="ESCALATE_TO_MERCHANT",
                    score_band=score_result.score_band,
                )

        # 5. Passed all criteria -> Autonomous Recovery Eligible
        reason_codes.append("ELIGIBLE_FOR_AUTOMATED_RECOVERY")
        return EligibilityResult(
            outcome="AUTO_RECOVER",
            eligible=True,
            reason_codes=reason_codes,
            reason_summary=f"High viability opportunity (Score: {score_result.score}) eligible for automated recovery.",
            recommended_action_class="CREATE_RECOVERY_PAYMENT_LINK",
            score_band=score_result.score_band,
        )

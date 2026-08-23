from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.models import Order, RecoveryOpportunity, MerchantPolicy, RecoveryAction, OrderStatus, OpportunityStatus, ActionExecutionStatus
from app.services.recovery_scoring_service import RecoveryScoreResult


@dataclass(frozen=True)
class PolicyDecisionResult:
    decision: str  # "ALLOW", "BLOCK", "ESCALATE"
    reason_codes: List[str]
    human_readable_summary: str
    policy_version: str = "v1"
    effective_action: str = "CREATE_PAYMENT_LINK"


class PolicyEngine:
    """Deterministic policy and guard engine enforcing the 10 core safety invariants."""

    POLICY_VERSION = "v1"
    SYSTEM_GOVERNANCE_ACTIONS = {"ESCALATE_TO_MERCHANT", "NO_ACTION", "NO_ACTION_CLOSE"}

    @classmethod
    def normalize_action(cls, action_name: str) -> str:
        """Normalizes action aliases to canonical enum values."""
        normalized = action_name.strip()
        if normalized == "CREATE_RECOVERY_PAYMENT_LINK":
            return "CREATE_PAYMENT_LINK"
        return normalized

    @classmethod
    def evaluate(
        cls,
        proposed_action: str,
        opportunity: RecoveryOpportunity,
        order: Order,
        score_result: RecoveryScoreResult,
        policy: Optional[MerchantPolicy] = None,
        existing_actions: Optional[List[RecoveryAction]] = None,
    ) -> PolicyDecisionResult:
        reason_codes: List[str] = []
        action = cls.normalize_action(proposed_action)

        # ----------------------------------------------------
        # 1. Order-Paid Guard (INVARIANT 1) -> BLOCK
        # ----------------------------------------------------
        if order.status == OrderStatus.PAID:
            reason_codes.append("ORDER_ALREADY_PAID")
            return PolicyDecisionResult(
                decision="BLOCK",
                reason_codes=reason_codes,
                human_readable_summary="Order is already successfully paid. Further recovery is blocked.",
                policy_version=cls.POLICY_VERSION,
                effective_action="NO_ACTION",
            )

        # ----------------------------------------------------
        # 2. Terminal State Guard (INVARIANT 2) -> BLOCK
        # ----------------------------------------------------
        if opportunity.status in [OpportunityStatus.RECOVERED, OpportunityStatus.CLOSED_UNRECOVERED]:
            reason_codes.append("OPPORTUNITY_TERMINAL")
            return PolicyDecisionResult(
                decision="BLOCK",
                reason_codes=reason_codes,
                human_readable_summary=f"Opportunity is sealed in terminal state '{opportunity.status.value}'.",
                policy_version=cls.POLICY_VERSION,
                effective_action="NO_ACTION",
            )

        # ----------------------------------------------------
        # 3. System Governance Action Handling (ESCALATE / NO_ACTION)
        # ----------------------------------------------------
        if action == "ESCALATE_TO_MERCHANT":
            reason_codes.append("AI_PROPOSED_MERCHANT_ESCALATION")
            return PolicyDecisionResult(
                decision="ESCALATE",
                reason_codes=reason_codes,
                human_readable_summary="Action proposed manual merchant review and escalation.",
                policy_version=cls.POLICY_VERSION,
                effective_action="ESCALATE_TO_MERCHANT",
            )

        if action in ["NO_ACTION", "NO_ACTION_CLOSE"]:
            reason_codes.append("NO_RECOVERY_ACTION_REQUIRED")
            return PolicyDecisionResult(
                decision="BLOCK",
                reason_codes=reason_codes,
                human_readable_summary="Action proposed no recovery intervention.",
                policy_version=cls.POLICY_VERSION,
                effective_action="NO_ACTION",
            )

        # ----------------------------------------------------
        # 4. Action Allowlist Guard (INVARIANT 5) -> BLOCK
        # ----------------------------------------------------
        if policy and policy.allowed_actions:
            normalized_allowed = [cls.normalize_action(a) for a in policy.allowed_actions]
            if action not in normalized_allowed and action not in cls.SYSTEM_GOVERNANCE_ACTIONS:
                reason_codes.append(f"ACTION_NOT_IN_ALLOWLIST ({proposed_action})")
                return PolicyDecisionResult(
                    decision="BLOCK",
                    reason_codes=reason_codes,
                    human_readable_summary=f"Action '{proposed_action}' is not in merchant's allowed action set.",
                    policy_version=cls.POLICY_VERSION,
                    effective_action="NO_ACTION",
                )

        # ----------------------------------------------------
        # 5. Duplicate Active Action Guard -> BLOCK
        # ----------------------------------------------------
        if existing_actions:
            for act in existing_actions:
                if act.execution_status in [ActionExecutionStatus.PENDING, ActionExecutionStatus.SUCCESS]:
                    if cls.normalize_action(act.action_type.value) == action:
                        reason_codes.append("DUPLICATE_ACTIVE_ACTION")
                        return PolicyDecisionResult(
                            decision="BLOCK",
                            reason_codes=reason_codes,
                            human_readable_summary=f"An active action of type '{proposed_action}' already exists.",
                            policy_version=cls.POLICY_VERSION,
                            effective_action="NO_ACTION",
                        )

        # ----------------------------------------------------
        # 6. Auto Recovery Enabled Guard (INVARIANT 7) -> ESCALATE
        # ----------------------------------------------------
        if policy and not policy.auto_recovery_enabled:
            reason_codes.append("AUTO_RECOVERY_DISABLED")
            return PolicyDecisionResult(
                decision="ESCALATE",
                reason_codes=reason_codes,
                human_readable_summary="Autonomous recovery disabled by merchant policy. Escalated to manual review.",
                policy_version=cls.POLICY_VERSION,
                effective_action="ESCALATE_TO_MERCHANT",
            )

        # ----------------------------------------------------
        # 7. Max Retry Limit Guard (INVARIANT 3) -> ESCALATE
        # ----------------------------------------------------
        if policy and opportunity.attempt_count >= policy.max_retry_attempts:
            reason_codes.append(f"MAX_RETRIES_EXCEEDED ({opportunity.attempt_count} >= {policy.max_retry_attempts})")
            return PolicyDecisionResult(
                decision="ESCALATE",
                reason_codes=reason_codes,
                human_readable_summary=f"Exceeded maximum autonomous retry limit ({policy.max_retry_attempts} attempts). Escalated.",
                policy_version=cls.POLICY_VERSION,
                effective_action="ESCALATE_TO_MERCHANT",
            )

        # ----------------------------------------------------
        # 8. Amount Spending Cap Guard (INVARIANT 4) -> ESCALATE
        # ----------------------------------------------------
        if policy and order.amount_inr > policy.max_auto_recovery_amount_inr:
            reason_codes.append(
                f"AMOUNT_EXCEEDS_CAP (₹{order.amount_inr} > ₹{policy.max_auto_recovery_amount_inr})"
            )
            return PolicyDecisionResult(
                decision="ESCALATE",
                reason_codes=reason_codes,
                human_readable_summary=(
                    f"Order amount (₹{order.amount_inr}) exceeds merchant's autonomous recovery cap "
                    f"(₹{policy.max_auto_recovery_amount_inr}). Escalated for manual approval."
                ),
                policy_version=cls.POLICY_VERSION,
                effective_action="ESCALATE_TO_MERCHANT",
            )

        # ----------------------------------------------------
        # 9. Cooldown Interval Guard (INVARIANT 6) -> BLOCK / PENDING
        # ----------------------------------------------------
        if policy and opportunity.last_attempt_at and policy.cooldown_minutes > 0:
            now = datetime.now(timezone.utc)
            last_attempt = opportunity.last_attempt_at
            if last_attempt.tzinfo is None:
                last_attempt = last_attempt.replace(tzinfo=timezone.utc)

            cooldown_period = timedelta(minutes=policy.cooldown_minutes)
            if now < last_attempt + cooldown_period:
                remaining_seconds = int((last_attempt + cooldown_period - now).total_seconds())
                reason_codes.append(f"COOLDOWN_ACTIVE ({remaining_seconds}s remaining)")
                return PolicyDecisionResult(
                    decision="BLOCK",
                    reason_codes=reason_codes,
                    human_readable_summary=(
                        f"Cooldown active: {policy.cooldown_minutes}m required between recovery contacts. "
                        f"{remaining_seconds // 60}m {remaining_seconds % 60}s remaining."
                    ),
                    policy_version=cls.POLICY_VERSION,
                    effective_action="NO_ACTION",
                )

        # ----------------------------------------------------
        # 10. All Safety Rules Passed -> ALLOW (INVARIANT 9 & 10)
        # ----------------------------------------------------
        reason_codes.append("POLICY_APPROVED")
        return PolicyDecisionResult(
            decision="ALLOW",
            reason_codes=reason_codes,
            human_readable_summary=(
                f"Action '{action}' approved by Policy Engine ({cls.POLICY_VERSION}). "
                f"All spending limits, cooldowns, and status guards satisfied."
            ),
            policy_version=cls.POLICY_VERSION,
            effective_action=action,
        )

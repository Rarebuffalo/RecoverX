from app.services.agent.providers.base_provider import BaseLLMProvider
from app.schemas.agent import RecoveryAgentContext, AgentProposal
from app.models.enums import RecoveryActionType, DiagnosisCategory


class LocalDeterministicMockLLM(BaseLLMProvider):
    """Local deterministic mock provider for zero-cost, offline testing and CI evaluation."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-deterministic-v1"

    async def generate_proposal(self, context: RecoveryAgentContext) -> AgentProposal:
        cat_str = context.payment.failure_category.upper()

        # 1. Permanent Declines
        if "PERMANENT" in cat_str or "FRAUD" in cat_str or "STOLEN" in cat_str:
            return AgentProposal(
                diagnosis_category=DiagnosisCategory.PERMANENT_PAYMENT_FAILURE,
                diagnosis_summary="Payment declined due to permanent account closure, fraud flag, or hard card block.",
                recommended_action=RecoveryActionType.NO_ACTION,
                confidence=0.98,
                fallback_action=RecoveryActionType.NO_ACTION,
                decision_factors=[
                    "Hard bank decline / security block",
                    "Immediate retry will fail",
                    "Zero chargeback risk preservation",
                ],
            )

        # 2. Terminal Paid Orders
        if context.order.status in ["paid", "PAID"] or context.opportunity.status in ["RECOVERED", "recovered"]:
            return AgentProposal(
                diagnosis_category=DiagnosisCategory.UNKNOWN,
                diagnosis_summary="Order is already confirmed paid. No recovery action needed.",
                recommended_action=RecoveryActionType.NO_ACTION,
                confidence=0.99,
                fallback_action=RecoveryActionType.NO_ACTION,
                decision_factors=["Order is already paid in full"],
            )

        # 3. High Value / Max Retries Exceeded -> Escalate
        if context.order.amount_inr > context.policy.max_auto_recovery_amount_inr:
            return AgentProposal(
                diagnosis_category=DiagnosisCategory.INSUFFICIENT_FUNDS if "FUNDS" in cat_str else DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE,
                diagnosis_summary=f"High-ticket transaction (₹{context.order.amount_inr}) exceeds autonomous recovery threshold.",
                recommended_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
                confidence=0.88,
                fallback_action=RecoveryActionType.NO_ACTION,
                decision_factors=[
                    f"Order amount ₹{context.order.amount_inr} exceeds policy limit ₹{context.policy.max_auto_recovery_amount_inr}",
                    "Requires merchant financing or bespoke review",
                ],
            )

        # 4. Standard Recoverable Failures with Good Score -> Propose Link
        if ("TRANSIENT" in cat_str or "CUSTOMER_ACTION" in cat_str or "FUNDS" in cat_str or "METHOD" in cat_str) and context.recovery.score >= 60:
            if "CUSTOMER_ACTION" in cat_str:
                diag = DiagnosisCategory.CUSTOMER_ACTION_REQUIRED
            elif "FUNDS" in cat_str:
                diag = DiagnosisCategory.INSUFFICIENT_FUNDS
            elif "METHOD" in cat_str:
                diag = DiagnosisCategory.PAYMENT_METHOD_ISSUE
            else:
                diag = DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE

            return AgentProposal(
                diagnosis_category=diag,
                diagnosis_summary=(
                    "Payment failure appears transient or recoverable. "
                    "Customer historical behavior demonstrates high willingness to complete checkout."
                ),
                recommended_action=RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
                confidence=0.91,
                fallback_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
                decision_factors=[
                    f"Failure classified as {cat_str}",
                    f"Customer success rate {context.customer.success_rate * 100:.0f}%",
                    f"Deterministic score {context.recovery.score}/100 ({context.recovery.score_band})",
                    f"Recovery attempt count {context.opportunity.attempt_count}",
                ],
            )

        # 5. Default Fallback
        return AgentProposal(
            diagnosis_category=DiagnosisCategory.UNKNOWN,
            diagnosis_summary="Ambiguous failure signals require merchant oversight.",
            recommended_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
            confidence=0.70,
            fallback_action=RecoveryActionType.NO_ACTION,
            decision_factors=["Unclassified failure reason", "Conservative safety routing"],
        )

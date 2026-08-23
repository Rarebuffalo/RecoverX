from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    reason: str
    confidence: float
    is_transient: bool
    is_customer_actionable: bool
    is_permanent: bool


class FailureClassifier:
    """Deterministic classifier normalizing gateway error codes into domain failure categories."""

    TRANSIENT_CODES = {
        "BAD_REQUEST_GATEWAY_TIMEOUT",
        "GATEWAY_TIMEOUT",
        "GATEWAY_ERROR",
        "BANK_SWITCH_DOWN",
        "NETWORK_ERROR",
        "INTERNAL_SERVER_ERROR",
        "AUTH_TIMEOUT",
        "ACQUIRER_TIMEOUT",
    }

    CUSTOMER_ACTION_CODES = {
        "BAD_REQUEST_USER_CANCELLED",
        "USER_CANCELLED",
        "CUSTOMER_DROPPED",
        "OTP_EXPIRED",
        "3DS_DROPPED",
        "WINDOW_CLOSED",
        "APP_CLOSED",
        "PAYMENT_CANCELLED",
    }

    INSUFFICIENT_FUNDS_CODES = {
        "PAYMENT_CARD_INSUFFICIENT_FUNDS",
        "INSUFFICIENT_FUNDS",
        "ACCOUNT_BALANCE_LOW",
        "CREDIT_LIMIT_EXCEEDED",
    }

    METHOD_ISSUE_CODES = {
        "PAYMENT_CARD_INVALID_CVV",
        "INVALID_CVV",
        "CARD_EXPIRED",
        "PAYMENT_CARD_EXPIRED",
        "INVALID_PIN",
        "VPA_NOT_FOUND",
        "VPA_INACTIVE",
        "DAILY_LIMIT_EXCEEDED",
    }

    PERMANENT_CODES = {
        "PAYMENT_CARD_STOLEN",
        "CARD_STOLEN",
        "CARD_BLOCKED",
        "ACCOUNT_FROZEN",
        "FRAUD_SUSPECTED",
        "BANK_BLACKLIST",
        "MERCHANT_NOT_PERMITTED",
    }

    @classmethod
    def classify(
        cls,
        failure_code: Optional[str] = None,
        failure_reason: Optional[str] = None,
        method: Optional[str] = None,
    ) -> ClassificationResult:
        code = (failure_code or "").strip().upper()
        reason = (failure_reason or "").strip().lower()

        # 1. Permanent Declines
        if code in cls.PERMANENT_CODES or any(w in reason for w in ["stolen", "blocked", "fraud", "frozen", "blacklist"]):
            return ClassificationResult(
                category="PERMANENT",
                reason=f"Hard decline or security restriction ({code or 'reason keyword'})",
                confidence=0.95,
                is_transient=False,
                is_customer_actionable=False,
                is_permanent=True,
            )

        # 2. Transient Infrastructure Timeouts
        if code in cls.TRANSIENT_CODES or any(w in reason for w in ["timeout", "switch", "network", "gateway error", "server error"]):
            return ClassificationResult(
                category="TRANSIENT",
                reason=f"Transient network or banking gateway timeout ({code or 'timeout keyword'})",
                confidence=0.90,
                is_transient=True,
                is_customer_actionable=False,
                is_permanent=False,
            )

        # 3. Customer Dropout / Action Required
        if code in cls.CUSTOMER_ACTION_CODES or any(w in reason for w in ["cancelled", "canceled", "drawer", "otp", "dropped"]):
            return ClassificationResult(
                category="CUSTOMER_ACTION_REQUIRED",
                reason=f"Customer abandonment or authentication drop-off ({code or 'dropout keyword'})",
                confidence=0.88,
                is_transient=False,
                is_customer_actionable=True,
                is_permanent=False,
            )

        # 4. Insufficient Funds
        if code in cls.INSUFFICIENT_FUNDS_CODES or any(w in reason for w in ["insufficient", "balance", "limit exceeded"]):
            return ClassificationResult(
                category="INSUFFICIENT_FUNDS",
                reason=f"Account balance or credit limit decline ({code or 'insufficient balance'})",
                confidence=0.92,
                is_transient=False,
                is_customer_actionable=True,
                is_permanent=False,
            )

        # 5. Method Issues (Wrong CVV, Expired Card)
        if code in cls.METHOD_ISSUE_CODES or any(w in reason for w in ["cvv", "expired", "invalid pin", "vpa"]):
            return ClassificationResult(
                category="PAYMENT_METHOD_ISSUE",
                reason=f"Payment instrument specific credential error ({code or 'method error'})",
                confidence=0.85,
                is_transient=False,
                is_customer_actionable=True,
                is_permanent=False,
            )

        # 6. Default Unknown
        return ClassificationResult(
            category="UNKNOWN",
            reason="Unclassified payment failure code/reason",
            confidence=0.50,
            is_transient=False,
            is_customer_actionable=False,
            is_permanent=False,
        )

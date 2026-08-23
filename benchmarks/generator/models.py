from dataclasses import dataclass, field
from typing import Dict, Any, List
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ObservableCase:
    """Model-visible data: Strictly limited to telemetry observable at decision time. ZERO GROUND TRUTH."""
    case_id: str
    merchant_id: str
    merchant_segment: str
    auto_recovery_enabled: bool
    max_retry_attempts: int
    cooldown_minutes: int
    max_auto_recovery_amount_inr: float
    allowed_actions: List[str]
    order_amount_inr: float
    currency: str = "INR"
    order_status: str = "attempted"
    payment_method: str = "upi"
    failure_code: str = "BAD_REQUEST_GATEWAY_TIMEOUT"
    failure_reason: str = "Gateway switch timed out."
    attempt_count: int = 0
    customer_successful_orders: int = 5
    customer_total_orders: int = 6
    customer_lifetime_value_inr: float = 24500.0
    age_minutes: float = 12.0


@dataclass(frozen=True)
class BenchmarkTruth:
    """Hidden ground truth: Strictly isolated in the benchmark world. NEVER exposed to RecoverX."""
    case_id: str
    customer_true_segment: str
    failure_intrinsic_type: str
    true_recovery_probability: float
    is_actually_recoverable: bool  # Realized outcome under benchmark world RNG


@dataclass(frozen=True)
class SyntheticBenchmarkItem:
    observable: ObservableCase
    truth: BenchmarkTruth

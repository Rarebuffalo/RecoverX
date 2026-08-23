import random
import hashlib
from typing import List, Tuple
from benchmarks.generator.models import (
    ObservableCase,
    BenchmarkTruth,
    SyntheticBenchmarkItem,
)


class SyntheticBenchmarkGenerator:
    """Deterministic generator for synthetic payment recovery benchmark datasets."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_dataset(self, num_cases: int = 25000) -> Tuple[List[SyntheticBenchmarkItem], str]:
        """Generates exact num_cases of observable cases and isolated hidden truths."""
        self.rng = random.Random(self.seed)
        items: List[SyntheticBenchmarkItem] = []
        hasher = hashlib.sha256()

        for i in range(1, num_cases + 1):
            case_id = f"case_{self.seed}_{i:06d}"

            # 1. Merchant Profile
            m_rand = self.rng.random()
            if m_rand < 0.35:
                merchant_segment = "SMALL"
                merchant_id = "merch_small_01"
                max_auto_amount = 5000.0
                order_amount = round(self.rng.uniform(300.0, 4800.0), 2)
            elif m_rand < 0.80:
                merchant_segment = "MEDIUM"
                merchant_id = "merch_med_01"
                max_auto_amount = 15000.0
                order_amount = round(self.rng.uniform(1500.0, 14500.0), 2)
            else:
                merchant_segment = "LARGE"
                merchant_id = "merch_large_01"
                max_auto_amount = 50000.0
                order_amount = round(self.rng.uniform(8000.0, 65000.0), 2)

            auto_recovery_enabled = True
            max_retries = 2
            cooldown_min = 30
            allowed_actions = ["CREATE_RECOVERY_PAYMENT_LINK", "CREATE_PAYMENT_LINK"]

            # 2. Customer Behavioral Segment
            c_rand = self.rng.random()
            if c_rand < 0.30:
                cust_segment = "HIGH_LOYALTY"
                total_orders = self.rng.randint(6, 25)
                success_rate = self.rng.uniform(0.85, 0.98)
                succ_orders = int(round(total_orders * success_rate))
                ltv = round(succ_orders * (order_amount * self.rng.uniform(0.8, 1.3)), 2)
                base_willingness = 0.85
            elif c_rand < 0.65:
                cust_segment = "MEDIUM_LOYALTY"
                total_orders = self.rng.randint(3, 10)
                success_rate = self.rng.uniform(0.60, 0.80)
                succ_orders = int(round(total_orders * success_rate))
                ltv = round(succ_orders * (order_amount * self.rng.uniform(0.7, 1.1)), 2)
                base_willingness = 0.65
            elif c_rand < 0.85:
                cust_segment = "NEW_CUSTOMER"
                total_orders = 0
                succ_orders = 0
                ltv = 0.0
                base_willingness = 0.50
            elif c_rand < 0.95:
                cust_segment = "LOW_RELIABILITY"
                total_orders = self.rng.randint(3, 8)
                success_rate = self.rng.uniform(0.20, 0.40)
                succ_orders = int(round(total_orders * success_rate))
                ltv = round(succ_orders * order_amount, 2)
                base_willingness = 0.25
            else:
                cust_segment = "CHRONIC_DECLINE"
                total_orders = self.rng.randint(3, 12)
                success_rate = self.rng.uniform(0.0, 0.15)
                succ_orders = int(round(total_orders * success_rate))
                ltv = round(succ_orders * order_amount, 2)
                base_willingness = 0.05

            # 3. Failure Category & Telemetry
            f_rand = self.rng.random()
            if f_rand < 0.35:
                f_type = "TRANSIENT"
                f_code = "BAD_REQUEST_GATEWAY_TIMEOUT"
                f_reason = "Switch timeout contacting issuer handle."
                f_modifier = 0.30
                method = "upi" if self.rng.random() < 0.70 else "card"
            elif f_rand < 0.60:
                f_type = "CUSTOMER_ACTION_REQUIRED"
                f_code = "BAD_REQUEST_USER_CANCELLED"
                f_reason = "User abandoned 3DS confirmation screen."
                f_modifier = 0.18
                method = "upi" if self.rng.random() < 0.50 else "card"
            elif f_rand < 0.80:
                f_type = "INSUFFICIENT_FUNDS"
                f_code = "PAYMENT_CARD_INSUFFICIENT_FUNDS"
                f_reason = "Account balance insufficient."
                f_modifier = -0.10
                method = "card"
            elif f_rand < 0.90:
                f_type = "PAYMENT_METHOD_ISSUE"
                f_code = "GATEWAY_ERROR_DEBIT_FAILED"
                f_reason = "Card CVV mismatch or expired instrument."
                f_modifier = -0.20
                method = "card"
            elif f_rand < 0.97:
                f_type = "PERMANENT"
                f_code = "PAYMENT_RISK_FRAUD_DETECTED"
                f_reason = "Card reported stolen / hard security lock."
                f_modifier = -0.80
                method = "card"
            else:
                f_type = "UNKNOWN"
                f_code = "INTERNAL_SERVER_ERROR"
                f_reason = "Unclassified gateway response."
                f_modifier = -0.05
                method = "netbanking"

            # 4. Attempt History & Recency
            attempt_count = 0 if self.rng.random() < 0.75 else (1 if self.rng.random() < 0.70 else 2)
            age_minutes = round(self.rng.uniform(2.0, 180.0), 1)

            # 5. Independent Ground Truth Formulation (NO CIRCULAR LOGIC)
            # True probability based purely on synthetic physical factors:
            attempt_penalty = 0.18 * attempt_count
            amount_penalty = 0.05 if order_amount > 20000 else 0.0
            raw_prob = base_willingness + f_modifier - attempt_penalty - amount_penalty
            true_prob = max(0.01, min(0.98, raw_prob))

            # Realized ground truth outcome in the synthetic universe
            is_actually_recoverable = (self.rng.random() < true_prob)

            # Construct Observable Case (Sanitized, Model-Visible)
            obs = ObservableCase(
                case_id=case_id,
                merchant_id=merchant_id,
                merchant_segment=merchant_segment,
                auto_recovery_enabled=auto_recovery_enabled,
                max_retry_attempts=max_retries,
                cooldown_minutes=cooldown_min,
                max_auto_recovery_amount_inr=max_auto_amount,
                allowed_actions=allowed_actions,
                order_amount_inr=order_amount,
                payment_method=method,
                failure_code=f_code,
                failure_reason=f_reason,
                attempt_count=attempt_count,
                customer_successful_orders=succ_orders,
                customer_total_orders=total_orders,
                customer_lifetime_value_inr=ltv,
                age_minutes=age_minutes,
            )

            # Construct Hidden Truth (Benchmark-Only)
            truth = BenchmarkTruth(
                case_id=case_id,
                customer_true_segment=cust_segment,
                failure_intrinsic_type=f_type,
                true_recovery_probability=round(true_prob, 4),
                is_actually_recoverable=is_actually_recoverable,
            )

            hasher.update(f"{case_id}:{order_amount}:{true_prob}:{is_actually_recoverable}".encode("utf-8"))
            items.append(SyntheticBenchmarkItem(observable=obs, truth=truth))

        dataset_hash = hasher.hexdigest()
        return items, dataset_hash

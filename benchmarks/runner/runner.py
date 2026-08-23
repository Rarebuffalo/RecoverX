import time
import os
import sys
import math
import statistics
from typing import List, Dict, Any, Optional
from decimal import Decimal

API_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/api"))
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

from benchmarks.generator.models import SyntheticBenchmarkItem, ObservableCase, BenchmarkTruth
from benchmarks.evaluation.metrics import calculate_metrics, BenchmarkMetrics
from app.services.failure_classifier import FailureClassifier
from app.services.recovery_scoring_service import RecoveryScoringService


class BenchmarkRunner:
    """Executes high-throughput synthetic evaluation across baseline and RecoverX strategies."""

    def __init__(self, score_threshold: int = 60):
        self.score_threshold = score_threshold
        self.scoring_service = RecoveryScoringService()

    def run(
        self,
        items: List[SyntheticBenchmarkItem],
        strategy: str = "recoverx",
        threshold_override: Optional[int] = None,
        payment_link_cost: float = 2.0,
        ai_cost_per_case: float = 0.05,
    ) -> Dict[str, Any]:
        threshold = threshold_override if threshold_override is not None else self.score_threshold

        case_results: List[Dict[str, Any]] = []
        latencies_ms: List[float] = []
        total_revenue_at_risk = 0.0

        start_wall_clock = time.perf_counter()

        for item in items:
            obs = item.observable
            truth = item.truth
            total_revenue_at_risk += obs.order_amount_inr

            t0 = time.perf_counter()
            attempted = False
            recovered = False
            decision_code = "NO_ACTION"
            calculated_score = 0

            if strategy == "never_recover":
                attempted = False
                recovered = False
                decision_code = "NO_ACTION"

            elif strategy == "recover_all":
                # Blindly attempt everything under merchant auto-recovery limit
                if obs.order_amount_inr <= obs.max_auto_recovery_amount_inr and obs.auto_recovery_enabled:
                    attempted = True
                    recovered = truth.is_actually_recoverable
                    decision_code = "CREATE_PAYMENT_LINK"
                else:
                    attempted = False
                    recovered = False
                    decision_code = "ESCALATE_TO_MERCHANT"

            elif strategy == "first_failure_only":
                if (
                    obs.attempt_count <= 1
                    and obs.order_amount_inr <= obs.max_auto_recovery_amount_inr
                    and obs.auto_recovery_enabled
                ):
                    attempted = True
                    recovered = truth.is_actually_recoverable
                    decision_code = "CREATE_PAYMENT_LINK"
                else:
                    attempted = False
                    recovered = False
                    decision_code = "NO_ACTION"

            elif strategy == "recoverx":
                # ----------------------------------------------------
                # RECOVERX FULL DETERMINISTIC PIPELINE
                # ----------------------------------------------------
                # 1. Failure Classifier
                failure_cat = FailureClassifier.classify(obs.failure_code, obs.failure_reason)

                # 2. Additive Recovery Scoring
                cust_rate = (
                    obs.customer_successful_orders / obs.customer_total_orders
                    if obs.customer_total_orders > 0
                    else 0.0
                )
                
                score_res = self.scoring_service.calculate_direct_score(
                    failure_category=failure_cat.category,
                    customer_total_orders=obs.customer_total_orders,
                    customer_success_rate=cust_rate,
                    customer_ltv_inr=obs.customer_lifetime_value_inr,
                    attempt_count=obs.attempt_count,
                    order_amount_inr=obs.order_amount_inr,
                    age_minutes=obs.age_minutes,
                )
                calculated_score = score_res.score

                # 3. Policy & Safety Evaluation
                if not obs.auto_recovery_enabled:
                    attempted = False
                    decision_code = "ESCALATE"
                elif obs.attempt_count >= obs.max_retry_attempts:
                    attempted = False
                    decision_code = "ESCALATE"
                elif obs.order_amount_inr > obs.max_auto_recovery_amount_inr:
                    attempted = False
                    decision_code = "ESCALATE"
                elif score_res.score < threshold:
                    attempted = False
                    decision_code = "BLOCK"
                elif failure_cat.category == "PERMANENT":
                    attempted = False
                    decision_code = "BLOCK"
                else:
                    attempted = True
                    decision_code = "ALLOW"
                    recovered = truth.is_actually_recoverable

            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000)

            case_results.append({
                "case_id": obs.case_id,
                "amount": obs.order_amount_inr,
                "attempted_recovery": attempted,
                "recovered": recovered,
                "is_actually_recoverable": truth.is_actually_recoverable,
                "decision": decision_code,
                "score": calculated_score,
            })

        total_duration_sec = time.perf_counter() - start_wall_clock
        throughput_cps = round(len(items) / total_duration_sec, 1)

        metrics = calculate_metrics(
            total_cases=len(items),
            revenue_at_risk=total_revenue_at_risk,
            cases_results=case_results,
            payment_link_cost=payment_link_cost,
            ai_cost_per_case=ai_cost_per_case,
        )

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)
        latency_stats = {
            "mean_ms": round(statistics.mean(sorted_lat), 3) if n > 0 else 0.0,
            "median_ms": round(statistics.median(sorted_lat), 3) if n > 0 else 0.0,
            "p95_ms": round(sorted_lat[int(0.95 * n)], 3) if n > 0 else 0.0,
            "p99_ms": round(sorted_lat[int(0.99 * n)], 3) if n > 0 else 0.0,
        }

        return {
            "strategy": strategy,
            "threshold": threshold,
            "metrics": metrics,
            "throughput_cases_per_sec": throughput_cps,
            "duration_seconds": round(total_duration_sec, 3),
            "latency": latency_stats,
            "case_results": case_results,
        }

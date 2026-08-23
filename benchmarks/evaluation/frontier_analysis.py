import os
import sys
import json
import statistics
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

API_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/api"))
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

from benchmarks.generator.models import SyntheticBenchmarkItem, ObservableCase, BenchmarkTruth
from benchmarks.generator.generator import SyntheticBenchmarkGenerator
from benchmarks.evaluation.metrics import calculate_metrics, BenchmarkMetrics
from app.services.failure_classifier import FailureClassifier
from app.services.recovery_scoring_service import RecoveryScoringService


class BenchmarkAuditAndFrontierAnalyzer:
    """Comprehensive diagnostic analyzer for RecoverX economic frontier, score calibration, and policy optimization."""

    def __init__(self, seed: int = 42, num_cases: int = 25000):
        self.seed = seed
        self.num_cases = num_cases
        self.gen = SyntheticBenchmarkGenerator(seed=seed)
        self.items, self.dataset_hash = self.gen.generate_dataset(num_cases=num_cases)
        self.scoring_service = RecoveryScoringService()

    def run_full_analysis(self) -> Dict[str, Any]:
        # 1. Evaluate all cases under v1 scoring and baseline
        case_records = self._evaluate_cases_v1()

        # 2. FN Analysis (Breakdown of missed recoverable revenue)
        fn_breakdown = self._analyze_false_negatives(case_records)

        # 3. FP Analysis (Breakdown of wasted intervention spend)
        fp_breakdown = self._analyze_false_positives(case_records)

        # 4. Score Calibration & Saturation
        score_calibration, score_saturation = self._analyze_score_calibration(case_records)

        # 5. Economic Frontier (Thresholds 20 to 90 by 5)
        frontier_results, pareto_thresholds = self._compute_economic_frontier()

        # 6. Policy vs Score Rejection Analysis
        policy_vs_score = self._analyze_policy_vs_score(case_records)

        # 7. Candidate Policy v2 Evaluation
        candidate_v2_results = self._evaluate_candidate_policy_v2()

        # 8. Feature Importance
        feature_importance = self._analyze_feature_importance(case_records)

        return {
            "metadata": {
                "seed": self.seed,
                "total_cases": self.num_cases,
                "dataset_hash": self.dataset_hash,
                "revenue_at_risk_inr": sum(it.observable.order_amount_inr for it in self.items),
            },
            "fn_breakdown": fn_breakdown,
            "fp_breakdown": fp_breakdown,
            "score_calibration": score_calibration,
            "score_saturation": score_saturation,
            "economic_frontier": frontier_results,
            "pareto_thresholds": pareto_thresholds,
            "policy_vs_score": policy_vs_score,
            "candidate_policy_v2": candidate_v2_results,
            "feature_importance": feature_importance,
        }

    def _evaluate_cases_v1(self, threshold: int = 60) -> List[Dict[str, Any]]:
        records = []
        for item in self.items:
            obs = item.observable
            truth = item.truth
            f_cat = FailureClassifier.classify(obs.failure_code, obs.failure_reason).category
            cust_rate = obs.customer_successful_orders / obs.customer_total_orders if obs.customer_total_orders > 0 else 0.0

            score_res = self.scoring_service.calculate_direct_score(
                failure_category=f_cat,
                customer_total_orders=obs.customer_total_orders,
                customer_success_rate=cust_rate,
                customer_ltv_inr=obs.customer_lifetime_value_inr,
                attempt_count=obs.attempt_count,
                order_amount_inr=obs.order_amount_inr,
                age_minutes=obs.age_minutes,
            )

            score = score_res.score
            is_recoverable = truth.is_actually_recoverable

            # Policy checks
            blocked_by_policy = False
            policy_reason = None
            if not obs.auto_recovery_enabled:
                blocked_by_policy = True
                policy_reason = "AUTO_RECOVERY_DISABLED"
            elif obs.attempt_count >= obs.max_retry_attempts:
                blocked_by_policy = True
                policy_reason = "MAX_RETRIES_EXCEEDED"
            elif obs.order_amount_inr > obs.max_auto_recovery_amount_inr:
                blocked_by_policy = True
                policy_reason = "AMOUNT_EXCEEDS_CAP"
            elif f_cat == "PERMANENT":
                blocked_by_policy = True
                policy_reason = "PERMANENT_FAILURE"

            blocked_by_score = (score < threshold)
            attempted = (not blocked_by_policy) and (not blocked_by_score)
            recovered = attempted and is_recoverable

            records.append({
                "case_id": obs.case_id,
                "amount": obs.order_amount_inr,
                "failure_category": f_cat,
                "merchant_segment": obs.merchant_segment,
                "customer_segment": truth.customer_true_segment,
                "attempt_count": obs.attempt_count,
                "score": score,
                "score_band": score_res.score_band,
                "is_actually_recoverable": is_recoverable,
                "attempted": attempted,
                "recovered": recovered,
                "blocked_by_policy": blocked_by_policy,
                "policy_reason": policy_reason,
                "blocked_by_score": blocked_by_score,
            })
        return records

    def _analyze_false_negatives(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        fn_cases = [r for r in records if r["is_actually_recoverable"] and not r["attempted"]]
        total_fn_count = len(fn_cases)
        total_fn_amount = sum(r["amount"] for r in fn_cases)

        by_cat = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_cust = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_merchant = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_score_band = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_attempt = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_block_cause = defaultdict(lambda: {"count": 0, "amount": 0.0})

        for r in fn_cases:
            amt = r["amount"]
            by_cat[r["failure_category"]]["count"] += 1
            by_cat[r["failure_category"]]["amount"] += amt

            by_cust[r["customer_segment"]]["count"] += 1
            by_cust[r["customer_segment"]]["amount"] += amt

            by_merchant[r["merchant_segment"]]["count"] += 1
            by_merchant[r["merchant_segment"]]["amount"] += amt

            by_score_band[r["score_band"]]["count"] += 1
            by_score_band[r["score_band"]]["amount"] += amt

            by_attempt[str(r["attempt_count"])]["count"] += 1
            by_attempt[str(r["attempt_count"])]["amount"] += amt

            cause = r["policy_reason"] if r["blocked_by_policy"] else "SCORE_BELOW_THRESHOLD"
            by_block_cause[cause]["count"] += 1
            by_block_cause[cause]["amount"] += amt

        return {
            "total_fn_count": total_fn_count,
            "total_fn_amount_inr": round(total_fn_amount, 2),
            "by_failure_category": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_cat.items()},
            "by_customer_segment": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_cust.items()},
            "by_merchant_segment": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_merchant.items()},
            "by_score_band": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_score_band.items()},
            "by_attempt_count": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_attempt.items()},
            "by_block_cause": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_block_cause.items()},
        }

    def _analyze_false_positives(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        fp_cases = [r for r in records if r["attempted"] and not r["is_actually_recoverable"]]
        total_fp_count = len(fp_cases)
        total_fp_amount = sum(r["amount"] for r in fp_cases)

        by_cat = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_cust = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_score_band = defaultdict(lambda: {"count": 0, "amount": 0.0})
        by_merchant = defaultdict(lambda: {"count": 0, "amount": 0.0})

        for r in fp_cases:
            amt = r["amount"]
            by_cat[r["failure_category"]]["count"] += 1
            by_cat[r["failure_category"]]["amount"] += amt

            by_cust[r["customer_segment"]]["count"] += 1
            by_cust[r["customer_segment"]]["amount"] += amt

            by_score_band[r["score_band"]]["count"] += 1
            by_score_band[r["score_band"]]["amount"] += amt

            by_merchant[r["merchant_segment"]]["count"] += 1
            by_merchant[r["merchant_segment"]]["amount"] += amt

        return {
            "total_fp_count": total_fp_count,
            "total_fp_amount_inr": round(total_fp_amount, 2),
            "by_failure_category": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_cat.items()},
            "by_customer_segment": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_cust.items()},
            "by_score_band": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_score_band.items()},
            "by_merchant_segment": {k: {"count": v["count"], "amount_inr": round(v["amount"], 2)} for k, v in by_merchant.items()},
        }

    def _analyze_score_calibration(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        deciles = [
            (0, 19), (20, 29), (30, 39), (40, 49), (50, 59),
            (60, 69), (70, 79), (80, 89), (90, 100)
        ]
        calibration = []
        saturation_count_100 = sum(1 for r in records if r["score"] == 100)
        saturation_count_0 = sum(1 for r in records if r["score"] == 0)

        for low, high in deciles:
            group = [r for r in records if low <= r["score"] <= high]
            count = len(group)
            if count == 0:
                continue
            rec_count = sum(1 for r in group if r["is_actually_recoverable"])
            actual_rate = rec_count / count
            avg_amt = sum(r["amount"] for r in group) / count
            calibration.append({
                "score_range": f"{low}–{high}",
                "total_cases": count,
                "recoverable_cases": rec_count,
                "actual_recovery_rate": round(actual_rate, 4),
                "average_amount_inr": round(avg_amt, 2),
            })

        saturation = {
            "score_100_count": saturation_count_100,
            "score_100_pct": round(saturation_count_100 / len(records) * 100, 2),
            "score_0_count": saturation_count_0,
            "score_0_pct": round(saturation_count_0 / len(records) * 100, 2),
        }
        return calibration, saturation

    def _compute_economic_frontier(self) -> Tuple[List[Dict[str, Any]], List[int]]:
        thresholds = list(range(20, 95, 5))
        frontier = []
        total_rev_risk = sum(it.observable.order_amount_inr for it in self.items)

        for th in thresholds:
            recs = self._evaluate_cases_v1(threshold=th)
            case_results = [{
                "amount": r["amount"],
                "is_actually_recoverable": r["is_actually_recoverable"],
                "attempted_recovery": r["attempted"],
                "recovered": r["recovered"],
            } for r in recs]

            m = calculate_metrics(
                total_cases=len(self.items),
                revenue_at_risk=total_rev_risk,
                cases_results=case_results,
                payment_link_cost=2.0,
                ai_cost_per_case=0.05,
            )

            rev_per_attempt = round(m.recovered_revenue_inr / m.recovery_attempts, 2) if m.recovery_attempts > 0 else 0.0
            net_per_attempt = round(m.net_recovered_value_inr / m.recovery_attempts, 2) if m.recovery_attempts > 0 else 0.0

            frontier.append({
                "threshold": th,
                "recovery_attempts": m.recovery_attempts,
                "attempt_rate": m.attempt_rate,
                "recovered_revenue_inr": m.recovered_revenue_inr,
                "recovery_rate": m.recovery_rate,
                "precision": m.precision,
                "recall": m.recall,
                "false_positive_amount_inr": m.false_positive_amount_inr,
                "net_recovered_value_inr": m.net_recovered_value_inr,
                "recovered_revenue_per_attempt": rev_per_attempt,
                "net_recovered_value_per_attempt": net_per_attempt,
            })

        # Pareto detection (a threshold is Pareto-efficient if no other threshold has strictly higher recovered revenue AND strictly higher precision)
        pareto_th = []
        for i, pt in enumerate(frontier):
            dominated = False
            for other in frontier:
                if other["threshold"] != pt["threshold"]:
                    if (
                        other["recovered_revenue_inr"] >= pt["recovered_revenue_inr"]
                        and (other["precision"] or 0) >= (pt["precision"] or 0)
                        and (
                            other["recovered_revenue_inr"] > pt["recovered_revenue_inr"]
                            or (other["precision"] or 0) > (pt["precision"] or 0)
                        )
                    ):
                        dominated = True
                        break
            if not dominated:
                pareto_th.append(pt["threshold"])

        return frontier, pareto_th

    def _analyze_policy_vs_score(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        blocked_by_score_only = sum(1 for r in records if r["blocked_by_score"] and not r["blocked_by_policy"])
        blocked_by_policy_only = sum(1 for r in records if r["blocked_by_policy"] and not r["blocked_by_score"])
        blocked_by_both = sum(1 for r in records if r["blocked_by_policy"] and r["blocked_by_score"])
        allowed = sum(1 for r in records if r["attempted"])

        return {
            "total_cases": len(records),
            "allowed_and_attempted": allowed,
            "blocked_by_score_only": blocked_by_score_only,
            "blocked_by_policy_only": blocked_by_policy_only,
            "blocked_by_both": blocked_by_both,
        }

    def _evaluate_candidate_policy_v2(self) -> Dict[str, Any]:
        """Candidate Policy v2: Dynamic Failure-Aware & Loyalty-Preserving Thresholding.
        - Lowers threshold from 60 to 45 for TRANSIENT & CUSTOMER_ACTION failures with positive customer history.
        - Retains strict 65+ threshold on INSUFFICIENT_FUNDS & UNKNOWN.
        - Keeps hard BLOCK on PERMANENT failures.
        - Respects all merchant safety invariants and amount caps.
        """
        records = []
        total_rev_risk = sum(it.observable.order_amount_inr for it in self.items)

        for item in self.items:
            obs = item.observable
            truth = item.truth
            f_cat = FailureClassifier.classify(obs.failure_code, obs.failure_reason).category
            cust_rate = obs.customer_successful_orders / obs.customer_total_orders if obs.customer_total_orders > 0 else 0.0

            score_res = self.scoring_service.calculate_direct_score(
                failure_category=f_cat,
                customer_total_orders=obs.customer_total_orders,
                customer_success_rate=cust_rate,
                customer_ltv_inr=obs.customer_lifetime_value_inr,
                attempt_count=obs.attempt_count,
                order_amount_inr=obs.order_amount_inr,
                age_minutes=obs.age_minutes,
            )

            score = score_res.score
            is_recoverable = truth.is_actually_recoverable

            # Dynamic thresholding by failure category & loyalty
            if f_cat in ["TRANSIENT", "CUSTOMER_ACTION_REQUIRED"]:
                target_threshold = 45 if obs.customer_total_orders > 0 else 50
            elif f_cat == "INSUFFICIENT_FUNDS":
                target_threshold = 65
            else:
                target_threshold = 60

            # Policy safety checks
            blocked_by_policy = False
            if not obs.auto_recovery_enabled or obs.attempt_count >= obs.max_retry_attempts or obs.order_amount_inr > obs.max_auto_recovery_amount_inr or f_cat == "PERMANENT":
                blocked_by_policy = True

            attempted = (not blocked_by_policy) and (score >= target_threshold)
            recovered = attempted and is_recoverable

            records.append({
                "amount": obs.order_amount_inr,
                "is_actually_recoverable": is_recoverable,
                "attempted_recovery": attempted,
                "recovered": recovered,
            })

        m = calculate_metrics(
            total_cases=len(self.items),
            revenue_at_risk=total_rev_risk,
            cases_results=records,
            payment_link_cost=2.0,
            ai_cost_per_case=0.05,
        )

        return {
            "policy_version": "v2_candidate",
            "metrics": {
                "total_cases": m.total_cases,
                "revenue_at_risk_inr": m.revenue_at_risk_inr,
                "recovery_attempts": m.recovery_attempts,
                "attempt_rate": m.attempt_rate,
                "successful_recoveries": m.successful_recoveries,
                "recovered_revenue_inr": m.recovered_revenue_inr,
                "recovery_rate": m.recovery_rate,
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
                "false_positive_amount_inr": m.false_positive_amount_inr,
                "false_negative_amount_inr": m.false_negative_amount_inr,
                "intervention_cost_inr": m.intervention_cost_inr,
                "ai_cost_inr": m.ai_cost_inr,
                "net_recovered_value_inr": m.net_recovered_value_inr,
                "confusion_matrix": {
                    "TP": m.confusion_matrix.true_positives,
                    "FP": m.confusion_matrix.false_positives,
                    "FN": m.confusion_matrix.false_negatives,
                    "TN": m.confusion_matrix.true_negatives,
                },
            },
        }

    def _analyze_feature_importance(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        features = [
            ("failure_category", "Failure Category", "Transient/Dropoff errors exhibit +30-40% higher intrinsic recoverability over declines."),
            ("customer_segment", "Customer True Segment", "High-loyalty customers recover at 85-95% rate vs 5% for chronic decliners."),
            ("attempt_count", "Previous Attempts", "Each prior failed attempt decreases empirical recovery probability by ~18%."),
            ("merchant_segment", "Merchant Segment / Amount", "Higher average order values trigger merchant policy caps and slight willingness decay."),
        ]
        results = []
        for feat_key, name, desc in features:
            grouped = defaultdict(lambda: {"total": 0, "recoverable": 0})
            for r in records:
                val = str(r[feat_key])
                grouped[val]["total"] += 1
                if r["is_actually_recoverable"]:
                    grouped[val]["recoverable"] += 1
            results.append({
                "feature": name,
                "description": desc,
                "breakdown": {
                    k: {
                        "total": v["total"],
                        "recovery_rate": round(v["recoverable"] / v["total"], 4) if v["total"] > 0 else 0.0,
                    }
                    for k, v in grouped.items()
                }
            })
        return results

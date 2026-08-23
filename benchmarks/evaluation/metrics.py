from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class ConfusionMatrix:
    true_positives: int  # RecoverX attempted AND payment actually succeeded
    false_positives: int  # RecoverX attempted BUT payment failed (wasted cost)
    false_negatives: int  # RecoverX did NOT attempt, but case was actually recoverable (missed revenue)
    true_negatives: int  # RecoverX did NOT attempt, and case was indeed unrecoverable


@dataclass(frozen=True)
class BenchmarkMetrics:
    total_cases: int
    revenue_at_risk_inr: float
    total_recoverable_cases: int
    total_unrecoverable_cases: int
    
    # Decisions & Attempts
    recovery_attempts: int
    attempt_rate: float
    successful_recoveries: int
    recovered_revenue_inr: float
    recovery_rate: float  # Recovered Revenue / Revenue at Risk
    
    # Classification Performance
    confusion_matrix: ConfusionMatrix
    precision: Optional[float]  # TP / (TP + FP)
    recall: Optional[float]  # TP / (TP + FN)
    f1_score: Optional[float]
    
    # Financial & Error Accounting
    false_positive_amount_inr: float  # Amount of failed attempts
    false_negative_amount_inr: float  # Amount of missed recoverable opportunities
    
    # Cost Accounting (Configurable)
    intervention_cost_inr: float
    ai_cost_inr: float
    total_cost_inr: float
    net_recovered_value_inr: float  # Recovered Revenue - Total Cost


def calculate_metrics(
    total_cases: int,
    revenue_at_risk: float,
    cases_results: List[Dict[str, Any]],
    payment_link_cost: float = 2.0,
    ai_cost_per_case: float = 0.05,
) -> BenchmarkMetrics:
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    total_recoverable_cases = 0
    total_unrecoverable_cases = 0

    recovered_revenue = 0.0
    fp_amount = 0.0
    fn_amount = 0.0
    recovery_attempts = 0

    for r in cases_results:
        amount = r["amount"]
        is_actually_recoverable = r["is_actually_recoverable"]
        attempted = r["attempted_recovery"]
        recovered = r["recovered"]

        if is_actually_recoverable:
            total_recoverable_cases += 1
        else:
            total_unrecoverable_cases += 1

        if attempted:
            recovery_attempts += 1
            if recovered:
                tp += 1
                recovered_revenue += amount
            else:
                fp += 1
                fp_amount += amount
        else:
            if is_actually_recoverable:
                fn += 1
                fn_amount += amount
            else:
                tn += 1

    cm = ConfusionMatrix(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
    )

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None
    f1 = (
        round(2 * (precision * recall) / (precision + recall), 4)
        if (precision and recall and (precision + recall) > 0)
        else None
    )

    attempt_rate = round(recovery_attempts / total_cases, 4) if total_cases > 0 else 0.0
    recovery_rate = round(recovered_revenue / revenue_at_risk, 4) if revenue_at_risk > 0 else 0.0

    intervention_cost = round(recovery_attempts * payment_link_cost, 2)
    ai_cost = round(total_cases * ai_cost_per_case, 2)
    total_cost = round(intervention_cost + ai_cost, 2)
    net_value = round(recovered_revenue - total_cost, 2)

    return BenchmarkMetrics(
        total_cases=total_cases,
        revenue_at_risk_inr=round(revenue_at_risk, 2),
        total_recoverable_cases=total_recoverable_cases,
        total_unrecoverable_cases=total_unrecoverable_cases,
        recovery_attempts=recovery_attempts,
        attempt_rate=attempt_rate,
        successful_recoveries=tp,
        recovered_revenue_inr=round(recovered_revenue, 2),
        recovery_rate=recovery_rate,
        confusion_matrix=cm,
        precision=precision,
        recall=recall,
        f1_score=f1,
        false_positive_amount_inr=round(fp_amount, 2),
        false_negative_amount_inr=round(fn_amount, 2),
        intervention_cost_inr=intervention_cost,
        ai_cost_inr=ai_cost,
        total_cost_inr=total_cost,
        net_recovered_value_inr=net_value,
    )

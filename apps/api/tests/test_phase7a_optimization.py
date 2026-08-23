import pytest
from benchmarks.evaluation.frontier_analysis import BenchmarkAuditAndFrontierAnalyzer
from app.scripts.run_phase7a_analysis import run_adversarial_prompt_injection_suite


def test_frontier_monotonicity_and_pareto():
    analyzer = BenchmarkAuditAndFrontierAnalyzer(seed=42, num_cases=1000)
    frontier, pareto = analyzer._compute_economic_frontier()

    assert len(frontier) == 15  # 20 to 90 by 5
    assert len(pareto) > 0

    # Higher threshold should generally decrease attempt rate
    assert frontier[0]["attempt_rate"] >= frontier[-1]["attempt_rate"]


def test_score_calibration_monotonicity():
    analyzer = BenchmarkAuditAndFrontierAnalyzer(seed=42, num_cases=2500)
    records = analyzer._evaluate_cases_v1()
    calib, sat = analyzer._analyze_score_calibration(records)

    assert len(calib) > 0
    # Lowest decile rate vs highest decile rate
    low_rate = calib[0]["actual_recovery_rate"]
    high_rate = calib[-1]["actual_recovery_rate"]
    assert high_rate > low_rate


def test_false_negative_and_positive_breakdown():
    analyzer = BenchmarkAuditAndFrontierAnalyzer(seed=42, num_cases=1000)
    records = analyzer._evaluate_cases_v1(threshold=60)
    fn = analyzer._analyze_false_negatives(records)
    fp = analyzer._analyze_false_positives(records)

    assert fn["total_fn_count"] >= 0
    assert fp["total_fp_count"] >= 0

    # Ensure sum of categories equals total
    cat_fn_sum = sum(v["count"] for v in fn["by_failure_category"].values())
    assert cat_fn_sum == fn["total_fn_count"]

    cat_fp_sum = sum(v["count"] for v in fp["by_failure_category"].values())
    assert cat_fp_sum == fp["total_fp_count"]


def test_candidate_policy_v2_economic_metrics():
    analyzer = BenchmarkAuditAndFrontierAnalyzer(seed=42, num_cases=1500)
    v2_res = analyzer._evaluate_candidate_policy_v2()

    m = v2_res["metrics"]
    assert m["total_cases"] == 1500
    assert m["recovery_attempts"] > 0
    assert m["precision"] > 0.65
    assert m["net_recovered_value_inr"] > 0.0


def test_adversarial_prompt_injection_suite_containment():
    res = run_adversarial_prompt_injection_suite()
    assert res["total_adversarial_tests"] == 4
    assert res["all_passed"] is True
    for item in res["test_results"]:
        assert item["schema_contained"] is True

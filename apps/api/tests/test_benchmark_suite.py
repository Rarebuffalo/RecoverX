import pytest
from benchmarks.generator.generator import SyntheticBenchmarkGenerator
from benchmarks.runner.runner import BenchmarkRunner
from app.schemas.agent import (
    RecoveryAgentContext,
    OpportunityContext,
    OrderContext,
    CustomerAggregateContext,
    PaymentAttemptContext,
    DeterministicScoreContext,
    PolicyLimitsContext,
)


def test_exact_transaction_count():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items, d_hash = gen.generate_dataset(num_cases=500)
    assert len(items) == 500
    assert len(d_hash) == 64


def test_seeded_determinism_and_stable_ids():
    gen1 = SyntheticBenchmarkGenerator(seed=42)
    items1, hash1 = gen1.generate_dataset(num_cases=100)

    gen2 = SyntheticBenchmarkGenerator(seed=42)
    items2, hash2 = gen2.generate_dataset(num_cases=100)

    assert hash1 == hash2
    for i1, i2 in zip(items1, items2):
        assert i1.observable.case_id == i2.observable.case_id
        assert i1.observable.order_amount_inr == i2.observable.order_amount_inr
        assert i1.truth.true_recovery_probability == i2.truth.true_recovery_probability
        assert i1.truth.is_actually_recoverable == i2.truth.is_actually_recoverable


def test_ground_truth_isolation_and_no_data_leakage():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items, _ = gen.generate_dataset(num_cases=50)

    for item in items:
        obs = item.observable
        truth = item.truth

        # 1. ObservableCase must NOT have ground truth attributes
        assert not hasattr(obs, "true_recovery_probability")
        assert not hasattr(obs, "is_actually_recoverable")
        assert not hasattr(obs, "customer_true_segment")

        # 2. RecoveryAgentContext must NOT leak truth
        context = RecoveryAgentContext(
            opportunity=OpportunityContext(
                id=obs.case_id,
                status="DETECTED",
                revenue_at_risk_inr=obs.order_amount_inr,
                attempt_count=obs.attempt_count,
            ),
            order=OrderContext(
                amount_inr=obs.order_amount_inr,
                currency=obs.currency,
                status=obs.order_status,
            ),
            customer=CustomerAggregateContext(
                successful_orders=obs.customer_successful_orders,
                total_orders=obs.customer_total_orders,
                success_rate=obs.customer_successful_orders / obs.customer_total_orders if obs.customer_total_orders > 0 else 0.0,
                lifetime_value_inr=obs.customer_lifetime_value_inr,
            ),
            payment=PaymentAttemptContext(
                method=obs.payment_method,
                failure_category="TRANSIENT",
                failure_code=obs.failure_code,
                failure_reason=obs.failure_reason,
            ),
            recovery=DeterministicScoreContext(
                score=75,
                score_band="MEDIUM",
                eligibility="AUTO_RECOVER",
            ),
            policy=PolicyLimitsContext(
                auto_recovery_enabled=obs.auto_recovery_enabled,
                max_retry_attempts=obs.max_retry_attempts,
                cooldown_minutes=obs.cooldown_minutes,
                max_auto_recovery_amount_inr=obs.max_auto_recovery_amount_inr,
                allowed_actions=obs.allowed_actions,
            ),
            available_actions=obs.allowed_actions,
        )

        serialized = context.model_dump_json()
        assert "true_recovery_probability" not in serialized
        assert "is_actually_recoverable" not in serialized
        assert str(truth.true_recovery_probability) not in serialized


def test_baseline_never_recover():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items, _ = gen.generate_dataset(num_cases=200)

    runner = BenchmarkRunner(score_threshold=60)
    res = runner.run(items, strategy="never_recover")

    m = res["metrics"]
    assert m.recovery_attempts == 0
    assert m.recovered_revenue_inr == 0.0
    assert m.recovery_rate == 0.0
    assert m.confusion_matrix.true_positives == 0
    assert m.confusion_matrix.false_positives == 0


def test_baseline_recover_all():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items, _ = gen.generate_dataset(num_cases=200)

    runner = BenchmarkRunner(score_threshold=60)
    res = runner.run(items, strategy="recover_all")

    m = res["metrics"]
    assert m.recovery_attempts > 0
    assert m.recovered_revenue_inr > 0.0
    assert m.confusion_matrix.false_positives > 0


def test_recoverx_strategy_precision_and_policy():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items, _ = gen.generate_dataset(num_cases=500)

    runner = BenchmarkRunner(score_threshold=60)
    rx_res = runner.run(items, strategy="recoverx", threshold_override=60)
    ra_res = runner.run(items, strategy="recover_all")

    rx_m = rx_res["metrics"]
    ra_m = ra_res["metrics"]

    assert rx_m.precision > ra_m.precision
    assert rx_m.false_positive_amount_inr < ra_m.false_positive_amount_inr


def test_reproducibility_of_benchmark_run():
    gen = SyntheticBenchmarkGenerator(seed=42)
    items1, _ = gen.generate_dataset(num_cases=1000)
    items2, _ = gen.generate_dataset(num_cases=1000)

    runner = BenchmarkRunner(score_threshold=60)
    res1 = runner.run(items1, strategy="recoverx")
    res2 = runner.run(items2, strategy="recoverx")

    m1 = res1["metrics"]
    m2 = res2["metrics"]

    assert m1.recovery_attempts == m2.recovery_attempts
    assert m1.recovered_revenue_inr == m2.recovered_revenue_inr
    assert m1.confusion_matrix == m2.confusion_matrix
    assert m1.precision == m2.precision
    assert m1.recall == m2.recall

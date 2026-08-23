import argparse
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import json
from benchmarks.generator.generator import SyntheticBenchmarkGenerator
from benchmarks.runner.runner import BenchmarkRunner


def main():
    parser = argparse.ArgumentParser(description="Run single strategy benchmark.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--transactions", type=int, default=25000)
    parser.add_argument("--strategy", type=str, default="recoverx", choices=["recoverx", "recover_all", "never_recover", "first_failure_only"])
    parser.add_argument("--threshold", type=int, default=60)
    args = parser.parse_args()

    gen = SyntheticBenchmarkGenerator(seed=args.seed)
    items, dataset_hash = gen.generate_dataset(num_cases=args.transactions)

    runner = BenchmarkRunner(score_threshold=args.threshold)
    res = runner.run(items, strategy=args.strategy, threshold_override=args.threshold)
    m = res["metrics"]

    print(f"==================================================================")
    print(f"BENCHMARK RUN: {args.strategy.upper()} ({args.transactions:,} cases)")
    print(f"==================================================================")
    print(f"Dataset SHA-256:      {dataset_hash}")
    print(f"Duration:             {res['duration_seconds']}s ({res['throughput_cases_per_sec']:,} cases/sec)")
    print(f"Revenue at Risk:      ₹{m.revenue_at_risk_inr:,.2f}")
    print(f"Recovery Attempts:    {m.recovery_attempts:,} ({m.attempt_rate*100:.1f}%)")
    print(f"Recovered Revenue:    ₹{m.recovered_revenue_inr:,.2f} ({m.recovery_rate*100:.1f}%)")
    print(f"Precision:            {m.precision*100 if m.precision else 0.0:.1f}%")
    print(f"Recall:               {m.recall*100 if m.recall else 0.0:.1f}%")
    print(f"False Pos. Amount:    ₹{m.false_positive_amount_inr:,.2f}")
    print(f"Net Recovered Value:  ₹{m.net_recovered_value_inr:,.2f}")
    print(f"==================================================================")


if __name__ == "__main__":
    main()

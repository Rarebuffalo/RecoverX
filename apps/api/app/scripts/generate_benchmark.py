import argparse
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.generator.generator import SyntheticBenchmarkGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic payment recovery benchmark dataset.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for deterministic generation (default: 42)")
    parser.add_argument("--transactions", type=int, default=25000, help="Total transaction count (default: 25000)")
    args = parser.parse_args()

    print(f"==================================================================")
    print(f"RECOVERX DETERMINISTIC BENCHMARK GENERATOR")
    print(f"==================================================================")
    print(f"Seed:               {args.seed}")
    print(f"Transaction Count:  {args.transactions:,}")

    gen = SyntheticBenchmarkGenerator(seed=args.seed)
    items, dataset_hash = gen.generate_dataset(num_cases=args.transactions)

    recoverable_count = sum(1 for it in items if it.truth.is_actually_recoverable)
    total_rev_at_risk = sum(it.observable.order_amount_inr for it in items)

    print(f"\n[Generation Complete]")
    print(f"Total Cases:        {len(items):,}")
    print(f"Dataset SHA-256:    {dataset_hash}")
    print(f"Revenue at Risk:    ₹{total_rev_at_risk:,.2f}")
    print(f"True Recoverable:   {recoverable_count:,} ({recoverable_count / len(items) * 100:.1f}%)")
    print(f"True Unrecoverable: {len(items) - recoverable_count:,} ({(len(items) - recoverable_count) / len(items) * 100:.1f}%)")
    print(f"==================================================================")


if __name__ == "__main__":
    main()

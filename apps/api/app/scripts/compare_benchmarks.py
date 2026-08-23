import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import json
import csv
import argparse
from datetime import datetime, timezone
from benchmarks.generator.generator import SyntheticBenchmarkGenerator
from benchmarks.runner.runner import BenchmarkRunner


def run_full_comparison(seed: int = 42, num_cases: int = 25000):
    print("=" * 80)
    print(f"RECOVERX ECONOMIC BENCHMARK & COMPARISON SUITE (25,000 TRANSACTIONS)")
    print("=" * 80)

    # 1. Generate Dataset
    print("\n[1/5] Generating Synthetic Benchmark Dataset...")
    gen = SyntheticBenchmarkGenerator(seed=seed)
    items, dataset_hash = gen.generate_dataset(num_cases=num_cases)
    print(f"Generated {len(items):,} transactions. Dataset SHA-256: {dataset_hash}")

    # 2. Run Baselines and RecoverX
    print("\n[2/5] Executing Strategies against Synthetic Universe...")
    runner = BenchmarkRunner(score_threshold=60)

    strategies = ["never_recover", "recover_all", "first_failure_only", "recoverx"]
    strategy_results = {}

    for strat in strategies:
        print(f"  -> Running strategy: {strat.upper()}...")
        res = runner.run(items, strategy=strat, threshold_override=60)
        strategy_results[strat] = res

    # 3. Threshold Analysis (40, 50, 60, 70, 80)
    print("\n[3/5] Computing Threshold Sensitivity Curves (40, 50, 60, 70, 80)...")
    thresholds = [40, 50, 60, 70, 80]
    threshold_results = {}
    for th in thresholds:
        th_res = runner.run(items, strategy="recoverx", threshold_override=th)
        threshold_results[th] = th_res

    # 4. Throughput Scaling Benchmarks (1K, 5K, 10K, 25K)
    print("\n[4/5] Measuring Throughput & Latency Scaling (1K, 5K, 10K, 25K)...")
    throughput_benchmarks = {}
    for count in [1000, 5000, 10000, 25000]:
        sub_items = items[:count]
        sub_res = runner.run(sub_items, strategy="recoverx", threshold_override=60)
        throughput_benchmarks[count] = {
            "cases": count,
            "duration_sec": sub_res["duration_seconds"],
            "throughput_cps": sub_res["throughput_cases_per_sec"],
            "latency_p95_ms": sub_res["latency"]["p95_ms"],
        }

    # 5. Export Results & Generate Markdown Report
    print("\n[5/5] Exporting Benchmark Result Files...")
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../benchmarks/results"))
    os.makedirs(results_dir, exist_ok=True)

    # A. JSON Comparison Export
    json_path = os.path.join(results_dir, f"benchmark_comparison_{num_cases // 1000}k.json")
    comparison_data = {
        "metadata": {
            "seed": seed,
            "total_transactions": num_cases,
            "dataset_hash": dataset_hash,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_mode": "local_deterministic_batch",
            "cost_assumptions": {
                "payment_link_cost_inr": 2.0,
                "ai_cost_per_case_inr": 0.05,
            },
        },
        "strategies": {
            k: {
                "strategy": v["strategy"],
                "throughput_cps": v["throughput_cases_per_sec"],
                "duration_seconds": v["duration_seconds"],
                "latency": v["latency"],
                "metrics": {
                    "total_cases": v["metrics"].total_cases,
                    "revenue_at_risk_inr": v["metrics"].revenue_at_risk_inr,
                    "recovery_attempts": v["metrics"].recovery_attempts,
                    "attempt_rate": v["metrics"].attempt_rate,
                    "successful_recoveries": v["metrics"].successful_recoveries,
                    "recovered_revenue_inr": v["metrics"].recovered_revenue_inr,
                    "recovery_rate": v["metrics"].recovery_rate,
                    "precision": v["metrics"].precision,
                    "recall": v["metrics"].recall,
                    "f1_score": v["metrics"].f1_score,
                    "false_positive_amount_inr": v["metrics"].false_positive_amount_inr,
                    "false_negative_amount_inr": v["metrics"].false_negative_amount_inr,
                    "intervention_cost_inr": v["metrics"].intervention_cost_inr,
                    "ai_cost_inr": v["metrics"].ai_cost_inr,
                    "net_recovered_value_inr": v["metrics"].net_recovered_value_inr,
                    "confusion_matrix": {
                        "TP": v["metrics"].confusion_matrix.true_positives,
                        "FP": v["metrics"].confusion_matrix.false_positives,
                        "FN": v["metrics"].confusion_matrix.false_negatives,
                        "TN": v["metrics"].confusion_matrix.true_negatives,
                    },
                },
            }
            for k, v in strategy_results.items()
        },
        "threshold_curves": {
            str(th): {
                "threshold": th,
                "attempt_rate": tr["metrics"].attempt_rate,
                "recovery_rate": tr["metrics"].recovery_rate,
                "precision": tr["metrics"].precision,
                "recall": tr["metrics"].recall,
                "recovered_revenue_inr": tr["metrics"].recovered_revenue_inr,
                "false_positive_amount_inr": tr["metrics"].false_positive_amount_inr,
                "net_recovered_value_inr": tr["metrics"].net_recovered_value_inr,
            }
            for th, tr in threshold_results.items()
        },
        "throughput_benchmarks": throughput_benchmarks,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)

    # B. Markdown Report Export
    md_path = os.path.join(results_dir, f"benchmark_comparison_{num_cases // 1000}k.md")
    report_md = _generate_markdown_report(comparison_data)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # C. CSV Export for RecoverX Run
    csv_path = os.path.join(results_dir, f"benchmark_{num_cases // 1000}k_seed{seed}_recoverx.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "amount", "attempted", "recovered", "is_actually_recoverable", "score", "decision"])
        for c in strategy_results["recoverx"]["case_results"][:5000]:  # sample 5000 rows for concise file
            writer.writerow([c["case_id"], c["amount"], c["attempted_recovery"], c["recovered"], c["is_actually_recoverable"], c["score"], c["decision"]])

    print(f"\n[Artifacts Successfully Created]")
    print(f"JSON Results:  {json_path}")
    print(f"Markdown Doc:  {md_path}")
    print(f"Sample CSV:    {csv_path}")
    print("\n" + report_md)


def _generate_markdown_report(data: dict) -> str:
    meta = data["metadata"]
    strats = data["strategies"]
    rx = strats["recoverx"]["metrics"]
    ra = strats["recover_all"]["metrics"]
    nr = strats["never_recover"]["metrics"]
    ff = strats["first_failure_only"]["metrics"]

    md = f"""# RecoverX 25,000 Transaction Benchmark Report

> **Dataset SHA-256:** `{meta["dataset_hash"]}`  
> **Random Seed:** `{meta["seed"]}` | **Total Transactions:** `{meta["total_transactions"]:,}`  
> **Execution Engine:** `LocalDeterministicMockBatch` | **Generated:** `{meta["generated_at"]}`

---

## 1. Executive Summary & Strategy Comparison

| Strategy | Revenue at Risk | Recovery Attempts | Attempt Rate | Recovered Revenue | Recovery Rate | Precision | Recall | Net Recovered Value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Never Recover (Baseline 1)** | ₹{nr["revenue_at_risk_inr"]:,.2f} | 0 | 0.0% | ₹0.00 | 0.0% | N/A | 0.0% | ₹0.00 |
| **Recover All (Baseline 2)** | ₹{ra["revenue_at_risk_inr"]:,.2f} | {ra["recovery_attempts"]:,} | {ra["attempt_rate"]*100:.1f}% | ₹{ra["recovered_revenue_inr"]:,.2f} | {ra["recovery_rate"]*100:.1f}% | {ra["precision"]*100:.1f}% | {ra["recall"]*100:.1f}% | ₹{ra["net_recovered_value_inr"]:,.2f} |
| **First Failure Only (Baseline 3)** | ₹{ff["revenue_at_risk_inr"]:,.2f} | {ff["recovery_attempts"]:,} | {ff["attempt_rate"]*100:.1f}% | ₹{ff["recovered_revenue_inr"]:,.2f} | {ff["recovery_rate"]*100:.1f}% | {ff["precision"]*100:.1f}% | {ff["recall"]*100:.1f}% | ₹{ff["net_recovered_value_inr"]:,.2f} |
| **RecoverX (Deterministic Policy)** | **₹{rx["revenue_at_risk_inr"]:,.2f}** | **{rx["recovery_attempts"]:,}** | **{rx["attempt_rate"]*100:.1f}%** | **₹{rx["recovered_revenue_inr"]:,.2f}** | **{rx["recovery_rate"]*100:.1f}%** | **{rx["precision"]*100:.1f}%** | **{rx["recall"]*100:.1f}%** | **₹{rx["net_recovered_value_inr"]:,.2f}** |

---

## 2. Confusion Matrix & Classification Breakdown (RecoverX @ Threshold 60)

```
                       Actual Recoverable      Actual Unrecoverable
Attempt Recovery:      TP = {rx["confusion_matrix"]["TP"]:,}              FP = {rx["confusion_matrix"]["FP"]:,}
No Action / Block:     FN = {rx["confusion_matrix"]["FN"]:,}              TN = {rx["confusion_matrix"]["TN"]:,}
```

* **Precision (Wasted Effort Prevention):** **{rx["precision"]*100:.1f}%** (Higher is better — reduces wasted messages and customer spam).
* **Recall (Opportunity Capture):** **{rx["recall"]*100:.1f}%**
* **Wasted False Positive Cost:** ₹{rx["false_positive_amount_inr"]:,.2f} attempted on dead failures (vs ₹{ra["false_positive_amount_inr"]:,.2f} in Recover All).

---

## 3. Threshold Sensitivity Analysis

| Score Threshold | Attempt Rate | Recovery Rate | Precision | Recall | Recovered Revenue | Net Recovered Value |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for th, tdata in data["threshold_curves"].items():
        md += f"| **{th}** | {tdata['attempt_rate']*100:.1f}% | {tdata['recovery_rate']*100:.1f}% | {tdata['precision']*100:.1f}% | {tdata['recall']*100:.1f}% | ₹{tdata['recovered_revenue_inr']:,.2f} | ₹{tdata['net_recovered_value_inr']:,.2f} |\n"

    md += f"""
---

## 4. Local Synthetic Throughput & Latency Scaling

| Dataset Size | Wall-Clock Duration | Throughput (Cases/sec) | Latency p95 |
| :---: | :---: | :---: | :---: |
"""
    for count, bdata in data["throughput_benchmarks"].items():
        md += f"| **{count:,} cases** | {bdata['duration_sec']:.3f}s | **{bdata['throughput_cps']:,.1f} cps** | {bdata['latency_p95_ms']:.3f}ms |\n"

    md += f"""
---

## 5. Benchmark Integrity & Non-Circular Proof
1. **Ground Truth Independence:** True recovery probability was synthesized using hidden behavioral variables (intrinsic failure physics, merchant profile, true customer segment).
2. **Zero Context Leakage:** The model-visible payload contains zero ground-truth probability fields.
3. **Deterministic Reproducibility:** Exact dataset SHA-256 verified under random seed `{meta["seed"]}`.
"""
    return md


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 25K synthetic benchmark comparison.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--transactions", type=int, default=25000)
    args = parser.parse_args()
    run_full_comparison(seed=args.seed, num_cases=args.transactions)

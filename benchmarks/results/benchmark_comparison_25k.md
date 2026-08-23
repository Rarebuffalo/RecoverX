# RecoverX 25,000 Transaction Benchmark Report

> **Dataset SHA-256:** `103b73203a98c949560e17098c6c8f843fa53539eb1e8c5ef1125070c452b488`  
> **Random Seed:** `42` | **Total Transactions:** `25,000`  
> **Execution Engine:** `LocalDeterministicMockBatch` | **Generated:** `2026-08-21T13:52:25.154190+00:00`

---

## 1. Executive Summary & Strategy Comparison

| Strategy | Revenue at Risk | Recovery Attempts | Attempt Rate | Recovered Revenue | Recovery Rate | Precision | Recall | Net Recovered Value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Never Recover (Baseline 1)** | ₹297,652,385.45 | 0 | 0.0% | ₹0.00 | 0.0% | N/A | 0.0% | ₹0.00 |
| **Recover All (Baseline 2)** | ₹297,652,385.45 | 23,645 | 94.6% | ₹131,634,818.73 | 44.2% | 60.8% | 94.8% | ₹131,586,278.73 |
| **First Failure Only (Baseline 3)** | ₹297,652,385.45 | 21,940 | 87.8% | ₹126,526,608.63 | 42.5% | 62.9% | 91.0% | ₹126,481,478.63 |
| **RecoverX (Deterministic Policy)** | **₹297,652,385.45** | **18,766** | **75.1%** | **₹120,477,413.85** | **40.5%** | **71.7%** | **88.7%** | **₹120,438,631.85** |

---

## 2. Confusion Matrix & Classification Breakdown (RecoverX @ Threshold 60)

```
                       Actual Recoverable      Actual Unrecoverable
Attempt Recovery:      TP = 13,448              FP = 5,318
No Action / Block:     FN = 1,720              TN = 4,514
```

* **Precision (Wasted Effort Prevention):** **71.7%** (Higher is better — reduces wasted messages and customer spam).
* **Recall (Opportunity Capture):** **88.7%**
* **Wasted False Positive Cost:** ₹46,659,742.25 attempted on dead failures (vs ₹88,255,925.04 in Recover All).

---

## 3. Threshold Sensitivity Analysis

| Score Threshold | Attempt Rate | Recovery Rate | Precision | Recall | Recovered Revenue | Net Recovered Value |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **40** | 80.9% | 42.3% | 68.0% | 90.7% | ₹126,014,760.21 | ₹125,973,042.21 |
| **50** | 78.7% | 41.8% | 69.5% | 90.2% | ₹124,454,637.66 | ₹124,414,047.66 |
| **60** | 75.1% | 40.5% | 71.7% | 88.7% | ₹120,477,413.85 | ₹120,438,631.85 |
| **70** | 67.8% | 37.5% | 75.0% | 83.8% | ₹111,596,271.04 | ₹111,561,137.04 |
| **80** | 58.5% | 33.0% | 79.0% | 76.2% | ₹98,299,445.92 | ₹98,268,935.92 |

---

## 4. Local Synthetic Throughput & Latency Scaling

| Dataset Size | Wall-Clock Duration | Throughput (Cases/sec) | Latency p95 |
| :---: | :---: | :---: | :---: |
| **1,000 cases** | 0.009s | **106,195.8 cps** | 0.011ms |
| **5,000 cases** | 0.048s | **103,592.7 cps** | 0.012ms |
| **10,000 cases** | 0.097s | **102,694.8 cps** | 0.013ms |
| **25,000 cases** | 0.260s | **96,238.2 cps** | 0.013ms |

---

## 5. Benchmark Integrity & Non-Circular Proof
1. **Ground Truth Independence:** True recovery probability was synthesized using hidden behavioral variables (intrinsic failure physics, merchant profile, true customer segment).
2. **Zero Context Leakage:** The model-visible payload contains zero ground-truth probability fields.
3. **Deterministic Reproducibility:** Exact dataset SHA-256 verified under random seed `42`.

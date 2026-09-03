# RecoverX: Autonomous AI Revenue Recovery Layer

> **An autonomous, policy-bounded revenue recovery platform that safely rescues dropped digital checkouts and failed payments via Razorpay payment rails.**

---

## What RecoverX Does

RecoverX detects checkout dropoffs and payment failures in real time, diagnoses root causes with AI reasoning, scores recoverability, enforces strict deterministic policy gates, and dispatches bounded payment recovery workflows.

$$\text{DETECT} \longrightarrow \text{DIAGNOSE} \longrightarrow \text{SCORE} \longrightarrow \text{POLICY GATE} \longrightarrow \text{EXECUTE} \longrightarrow \text{VERIFY} \longrightarrow \text{RECOVER}$$

1. **DETECT:** Ingests checkout dropoffs, gateway timeouts, and payment failure webhooks.
2. **DIAGNOSE:** Evaluates sanitized error telemetry using structured AI reasoning (`recovery-diagnostic-v1`).
3. **SCORE:** Calculates an interpretable, deterministic recoverability score ($0-100$).
4. **POLICY GATE:** Enforces 10 hard safety invariants (spending limits, cooldowns, idempotency).
5. **EXECUTE:** Dispatches bounded recovery actions (e.g. Razorpay Payment Links) with server-side amount authority.
6. **VERIFY:** Confirms HMAC-SHA256 signed payment webhooks from Razorpay before declaring success.
7. **RECOVER:** Settles verified recovered revenue into an immutable audit ledger.

---

## The Safety Model: Untrusted AI vs Authoritative Policy

```
[ Sanitized Telemetry ] ──> [ AI Diagnostic Agent ] ──> (Advisory Proposal)
                                                                 │
                                                                 ▼
[ Payment Context ]     ──> [ Deterministic Policy Gate ] ──> [ Bounded Executor ] ──> [ Razorpay ]
                                (Financial Authority)          (Idempotent Links)
```

* **The AI Agent is ADVISORY ONLY:** The LLM proposes diagnoses and recovery strategies. It has zero permissions to execute financial transactions, create database records, or modify order amounts.
* **The Policy Gate is the FINANCIAL AUTHORITY:** 100% of recovery actions must pass deterministic invariant rules before execution.
* **Bounded Execution:** Amounts are strictly computed server-side from order records.
* **Zero Blind Retries:** Indeterminate gateway timeouts are quarantined in `AMBIGUOUS / HELD` state until reconciliation.

---

## Runtime Modes

| Mode | Purpose | Razorpay Credentials | AI Engine | Payment Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Mode 1: Local Demo (Default)** | Offline pitch demonstration & development | Not Required (`LocalDeterministicMockAdapter`) | Zero-cost mock (`LocalDeterministicMockLLM`) | Simulated webhook capture |
| **Mode 2: Razorpay Test Mode** | Live buildathon evaluation with real test payment rails | Required (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) | Optional Gemini (`LLM_API_KEY`) or mock | Real Razorpay test payment link & webhook |
| **Mode 3: Production** | Enterprise multi-tenant deployment | Production merchant KYC & live keys | Production Gemini 2.5 Flash | Real-money settlement & reconciliation |

---

## Quickstart (Docker Compose)

The fastest way to launch the complete RecoverX stack:

```bash
# 1. Clone & Enter Repository
git clone https://github.com/Rarebuffalo/RecoverX.git
cd RecoverX

# 2. Copy Environment Template
cp .env.example .env

# 3. Start All Services (API, Web Dashboard, Postgres, Redis)
docker compose up --build
```

* **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
* **Work Queue:** [http://localhost:3000/opportunities](http://localhost:3000/opportunities)
* **Interactive Strategy Frontier:** [http://localhost:3000/dashboard/analytics](http://localhost:3000/dashboard/analytics)
* **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **API Health Probe:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Environment Variables

| Variable | Required? | Default / Mode 1 | Mode 2 (Razorpay Test) | Description |
| :--- | :---: | :--- | :--- | :--- |
| `ENVIRONMENT` | Yes | `development` | `development` | Runtime environment name |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` | `postgresql+asyncpg://...` | PostgreSQL async connection URI |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | `redis://localhost:6379/0` | Redis task queue & cache URI |
| `EXECUTION_MODE` | Yes | `local_deterministic` | `razorpay_sandbox` | Selects gateway execution adapter |
| `RAZORPAY_KEY_ID` | Mode 2 | *(empty)* | `rzp_test_...` | Razorpay Test Key ID |
| `RAZORPAY_KEY_SECRET` | Mode 2 | *(empty)* | `••••••••••••` | Razorpay Test Key Secret |
| `RAZORPAY_WEBHOOK_SECRET` | Mode 2 | *(empty)* | `••••••••••••` | Webhook HMAC verification secret |
| `LLM_PROVIDER` | No | `mock` | `gemini` or `mock` | AI diagnostic reasoning engine |
| `LLM_API_KEY` | If Gemini | *(empty)* | `••••••••••••` | Google Gemini API Key |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost:8000` | `http://localhost:8000` | Frontend-to-backend API URL |

---

## Pitch & Evaluation Scenarios

RecoverX includes 4 canonical scenarios in both local seed data and the Demo Center:

* **Scenario A — Safe Recovery (₹8,499):** Transient NPCI UPI timeout. High score ($87$). Policy: **`ALLOW`**. Recovery link generated and verified upon payment.
* **Scenario B — Policy Escalation (₹45,000):** High-ticket purchase exceeding the ₹15,000 autonomous policy limit. Policy: **`ESCALATE`** (Manual Review Required).
* **Scenario D — Ambiguous Timeout (₹3,250):** Gateway timeout with indeterminate switch state. Policy: **`AMBIGUOUS / HELD`** (Zero blind retries).
* **Scenario E — Hard Decline (₹6,500):** Stolen card / fraud report. Score $<20$. Policy: **`BLOCK`** (Permanently closed).

---

## Empirical Benchmark (25,000 Synthetic Cases)

> **Note on Benchmark Data:** The dataset evaluated on the Analytics page comprises 25,000 synthetic transaction records generated to benchmark Pareto frontiers and score calibration. The ₹120.48M metric represents simulated recovery yield across this synthetic dataset, not real merchant revenue.

* **Baseline A (Recover All / Naive):** Attempt Rate 94.6%, Precision 60.8%, Recall 94.8%.
* **RecoverX Policy V1 ($\tau=60$):** Attempt Rate 75.1%, Precision **71.7% (+10.9%)**, Recall 88.7%, False Positive Spend contained by -38%.
* **Candidate Policy V2:** Attempt Rate 81.5%, Precision 68.4%, Recall **92.1%**.

---

## Testing & Quality Assurance

```bash
# Run 75/75 Backend Unit & Integration Tests
cd apps/api
uv run pytest -v

# Run Frontend Linting & Production Build
cd apps/web
npm run lint
npm run build
```

---

## Documentation Links

* [Architecture & Security Model](docs/architecture.md)
* [API Reference](docs/api-reference.md)
* [Manual Testing & Demo Guide](docs/MANUAL_TESTING.md)
* [Razorpay Webhooks Integration](docs/razorpay-webhooks.md)
* [Payment Links Specification](docs/razorpay-payment-links.md)
* [Policy Engine & Invariants](docs/policy-engine.md)
* [AI Diagnostic Agent](docs/ai-agent.md)
* [Benchmark Methodology](docs/benchmark.md)

---

## License

MIT License. Developed for the Razorpay AI Buildathon 2026.

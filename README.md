# RecoverX: Autonomous AI Revenue Recovery Layer

> **Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery**  
> *Current Status: Phase 8 Complete — Submission Ready, Feature Frozen & Pitch Hardened*

---

## What is RecoverX?

**RecoverX** is an autonomous, policy-bounded revenue recovery platform for digital merchants. Digital commerce experiences 5%–18% revenue leakage from dropped checkouts, transient gateway timeouts, and payment declines. RecoverX closes the loop from real-time detection and AI diagnosis to deterministic policy gating and bounded recovery execution via Razorpay rails.

### Core Architectural Principle: The Untrusted AI Boundary
* **The LLM is Untrusted:** The AI agent acts exclusively as a diagnostic and strategy reasoning engine that proposes structured actions.
* **Deterministic Policy Gate:** 100% of financial actions are validated by a deterministic, zero-hallucination policy engine.
* **Bounded Execution:** Only authorized, idempotent payment links and retries can be dispatched to Razorpay Test APIs.
* **Immutable Audit Trail:** Every state change, policy check, and recovered rupee is recorded in an append-only audit ledger.

---

## Tech Stack

* **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16
* **AI Diagnostic Layer:** Structured JSON Agent (`recovery-diagnostic-v1`), Multi-provider abstraction (`LocalDeterministicMockLLM` + `GeminiLLMProvider`)
* **Execution & Settlement:** Dual Gateway Adapters (`RazorpaySandboxAdapter` + `LocalDeterministicMockAdapter`), Celery / Async Worker Pipeline, `RecoveryOutcomeService`
* **Task Broker & Cache:** Redis 7
* **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
* **Testing:** pytest, pytest-asyncio, aiosqlite, PostgreSQL integration test harness
* **DevOps:** Docker Compose, Makefile

---

## Milestone Progress

### Phase 1: Foundation & Canonical Payment Domain (Complete)
- [x] Monorepo structure (`apps/api`, `apps/web`, `docs`)
- [x] Docker Compose environment (`postgres`, `redis`, `api`, `web`)
- [x] Canonical payment domain model in PostgreSQL.
- [x] Seed data script (`python -m app.db.seed`) with Scenarios A, B, and C.
- [x] Liveness (`/health`) and Readiness (`/ready`) probes.

### Phase 2: Webhook Ingestion, Authentication & State Sync (Complete)
- [x] Cryptographic HMAC-SHA256 signature verification over exact raw request body bytes.
- [x] Atomic deduplication on `(provider, event_id)`.
- [x] Domain event handlers: `payment.failed`, `payment.captured`, `order.paid`, `payment_link.paid`.
- [x] Event precedence rules: `PAID / CAPTURED` dominates `FAILED`.
- [x] Automatic `RecoveryOpportunity` initialization in `DETECTED` state upon primary failure.

### Phase 3: Interpretable Scoring & Policy Engine (Complete)
- [x] Deterministic `FailureClassifier` normalizing error codes.
- [x] Additive, inspectable `RecoveryScoringService` ($0-100$ score with feature breakdown).
- [x] `RecoveryEligibilityService` (`AUTO_RECOVER`, `MANUAL_REVIEW`, `DO_NOT_RECOVER`).
- [x] Deterministic `PolicyEngine` enforcing the 10 Core Safety Invariants (`ALLOW`, `BLOCK`, `ESCALATE`).

### Phase 4: AI Diagnostic Agent (Proposal Mode Only) (Complete)
- [x] Multi-provider LLM abstraction (`BaseLLMProvider`, `LocalDeterministicMockLLM`, `GeminiLLMProvider`).
- [x] Zero-PII Context Sanitization via `RecoveryContextBuilder`.
- [x] Strict Prompt Injection defenses using delimited `<untrusted_recovery_context>` tags (`recovery-diagnostic-v1`).
- [x] Structured JSON output validation (`AgentProposal` with `DiagnosisCategory` & `RecoveryActionType`).
- [x] AI Model confidence decoupled from deterministic business recoverability score.
- [x] Graceful, deterministic fallback to `ESCALATE_TO_MERCHANT` on AI timeout/error.

### Phase 5: Bounded Financial Execution & Outcome Engine (Complete)
- [x] Verified Razorpay Payment Links API specification in `docs/razorpay-payment-links.md`.
- [x] Dual Gateway Adapters (`RazorpaySandboxAdapter` + `LocalDeterministicMockAdapter`).
- [x] Configurable execution modes (`local_deterministic`, `razorpay_sandbox`).
- [x] Execution state machine (`PENDING`, `QUEUED`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `AMBIGUOUS`, `CANCELLED`).
- [x] Strict deterministic action idempotency keying (`recovery:{opportunity_id}:attempt:{attempt_number}`).
- [x] Pre-execution safety checks (unpaid order verification, terminal opportunity seals, policy re-checks).
- [x] Authoritative server-side amount calculation (AI and client have zero influence on executed amount).
- [x] Provider error classification and `AMBIGUOUS` timeout handling without blind retries.
- [x] Celery background task worker integration (`execute_recovery_action_task`).
- [x] `RecoveryOutcomeService` verifying causal proof of captured payment before settling recovered revenue.
- [x] Prevention of double-counting on duplicate captured webhooks.
- [x] Developer payment simulation endpoint (`POST /api/v1/developer/simulate-payment-success`).
- [x] Next.js Command Center displaying real-time execution lifecycle and settled revenue metrics.
- [x] 100% passing automated test suite (63 tests).

---

## Quickstart & Local Setup

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+ (or `uv`)
- Node.js 18+ & npm

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Run with Docker Compose (Recommended)
```bash
docker compose up --build
```
* **Frontend Command Center:** [http://localhost:3000/opportunities](http://localhost:3000/opportunities)
* **API Documentation:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### 4. Run Backend & Migrations Locally
```bash
cd apps/api
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run Alembic Migrations
alembic upgrade head

# Seed Initial Demo Scenarios
python -m app.db.seed

# Run Evaluation CLI
python -m app.scripts.evaluate_recovery

# Run FastAPI Server
uvicorn app.main:app --reload --port 8000
```

### 5. Run Automated Tests
```bash
cd apps/api
pytest -v
```

---

## Pre-Seeded Development Scenarios

| Scenario | Order Amount | Failure Mode | Recovery Score | AI Proposal | Policy Decision | Execution & Outcome |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **Scenario A** | ₹8,499.00 | Gateway Timeout (UPI Intent) | **100/100 (HIGH)** | `CREATE_RECOVERY_PAYMENT_LINK` (91%) | **`ALLOW`** | **Payment Link Created** &rarr; Paid &rarr; **₹8,499 Recovered** |
| **Scenario B** | ₹45,000.00 | Insufficient Funds (2 Attempts) | **45/100 (LOW)** | `ESCALATE_TO_MERCHANT` (88%) | **`ESCALATE`** | Escalated to Merchant Dashboard |
| **Scenario C** | ₹4,999.00 | Paid / Recovered Transaction | **55/100 (LOW)** | `NO_ACTION` (99%) | **`BLOCK`** | Further Recovery Blocked (`ORDER_ALREADY_PAID`) |

---

## Architecture Reference
* [`docs/architecture.md`](file:///home/Krishna-Singh/RecoverX/docs/architecture.md)
* [`docs/execution-engine.md`](file:///home/Krishna-Singh/RecoverX/docs/execution-engine.md)
* [`docs/outcome-engine.md`](file:///home/Krishna-Singh/RecoverX/docs/outcome-engine.md)
* [`docs/razorpay-payment-links.md`](file:///home/Krishna-Singh/RecoverX/docs/razorpay-payment-links.md)
* [`docs/ai-agent.md`](file:///home/Krishna-Singh/RecoverX/docs/ai-agent.md)
* [`docs/policy-engine.md`](file:///home/Krishna-Singh/RecoverX/docs/policy-engine.md)
* [`docs/recovery-scoring.md`](file:///home/Krishna-Singh/RecoverX/docs/recovery-scoring.md)
* [`docs/razorpay-webhooks.md`](file:///home/Krishna-Singh/RecoverX/docs/razorpay-webhooks.md)

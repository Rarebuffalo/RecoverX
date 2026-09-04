# RecoverX Architecture & Domain Model

## 1. Domain Model Hierarchy

```
Merchant (Tenant Boundary)
 ├── MerchantPolicy (1:1 Multi-Attempt, Cap & Cooldown Rules)
 ├── Customers (1:N Profiles & LTV Metrics)
 ├── Orders (1:N Canonical Transactions)
 │    ├── PaymentAttempts (1:N Gateway Transactions)
 │    └── RecoveryOpportunity (1:1 Recovery Lifecycle Coordinator)
 │         ├── RecoveryDecisions (1:N Diagnostic Proposals & Policy Signals)
 │         ├── AgentRuns (1:N Auditable Execution Traces)
 │         └── RecoveryActions (1:N Gated Execution Units)
 └── AuditEvents (1:N Append-Only Event Stream)
```

## 2. Real-Time Ingestion, AI Diagnostic & Policy Gate Pipeline

```
Razorpay Webhook (POST /api/v1/webhooks/razorpay)
       │
       ▼
[Raw Body Capture] ──► [HMAC-SHA256 Signature Verification]
                               │
                               ▼
            [Atomic Deduplication on processed_webhooks]
                               │
                               ▼
                        [Event Router]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     payment.failed                        payment.captured
            │                                     │
            ▼                                     ▼
  [Payment Attempt: FAILED]             [Payment Attempt: CAPTURED]
  [Order: ATTEMPTED]                    [Order: PAID]
  [Opportunity: DETECTED]               [Opportunity: RECOVERED]
            │
            ▼
┌──────────────────────────────────────────────────────────────┐
│ DETERMINISTIC SCORING & CONTEXT BUILDER                      │
│                                                              │
│ 1. FailureClassifier (Normalized failure category)           │
│ 2. RecoveryScoringService (0–100 Inspectable features)       │
│ 3. RecoveryContextBuilder (ZERO PII, aggregated statistics)  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ UNTRUSTED AI DIAGNOSTIC RECOVERY AGENT                       │
│                                                              │
│ Versioned Prompt: "recovery-diagnostic-v1"                   │
│ Multi-Provider: LocalDeterministicMockLLM / GeminiProvider   │
│ Delimited Context: <untrusted_recovery_context>              │
│ Structured Output: AgentProposal (Pydantic validated)        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ DETERMINISTIC POLICY & GUARD ENGINE (v1)                     │
│                                                              │
│ Evaluates AI Proposal against 10 Core Invariants:            │
│  - Paid order guard -> BLOCK                                 │
│  - Terminal opportunity seal -> BLOCK                        │
│  - Action allowlist guard -> BLOCK                           │
│  - Max retry cap -> ESCALATE                                 │
│  - Spending threshold cap -> ESCALATE                        │
│  - Mandatory cooldown -> BLOCK                               │
│  - Kill-switch disabled -> ESCALATE                          │
│                                                              │
│ Outcomes: ALLOW / BLOCK / ESCALATE                           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ PERSISTENT AUDITABLE LEDGER                                  │
│                                                              │
│ 1. agent_runs (Latency, provider, model, error_code)         │
│ 2. recovery_decisions (Diagnostic proposal & policy signals) │
│ 3. audit_events (Append-only immutable audit trail)          │
└──────────────────────────────────────────────────────────────┘
```
## High Level Architecture
```
                    ┌──────────────────────────────┐
                    │     Cloud / Render / Docker  │
                    │                              │
Browser ───────────►│ Next.js Frontend             │
                    │       │                      │
                    │       ▼                      │
                    │ FastAPI API ◄────────────────┼──── Razorpay Test API
                    │   │      │                   │
                    │   │      └───────────────────┼──── Razorpay Webhooks
                    │   ▼                          │
                    │ PostgreSQL                   │
                    │                              │
                    │ Redis (Optional / Celery)    │
                    └──────────────────────────────┘
```
## 3. Core Safety Invariants (10 Invariant Truths)

1. **INVARIANT 1 (Paid Order Isolation):** A paid order can NEVER receive recovery approval under any circumstance.
2. **INVARIANT 2 (Terminal Opportunity Seal):** An opportunity marked `RECOVERED` or `CLOSED_UNRECOVERED` cannot be reopened.
3. **INVARIANT 3 (Retry Cap Enforcement):** Total autonomous attempts cannot exceed `merchant_policies.max_retry_attempts`.
4. **INVARIANT 4 (Financial Limit Protection):** Orders exceeding `merchant_policies.max_auto_recovery_amount_inr` require human approval.
5. **INVARIANT 5 (Strict Allowlist Control):** Action types outside `merchant_policies.allowed_actions` are blocked instantly.
6. **INVARIANT 6 (Cooldown Protection):** Automated contacts must honor `merchant_policies.cooldown_minutes` between attempts.
7. **INVARIANT 7 (Merchant Kill-Switch):** Toggling `auto_recovery_enabled = False` immediately escalates all automated recovery.
8. **INVARIANT 8 (Immutable Policy Versioning):** Every policy decision records the active `policy_version` (`v1`).
9. **INVARIANT 9 (Machine-Readable Explainability):** All decisions contain structured `reason_codes` and human-readable explanation strings.
10. **INVARIANT 10 (100% Determinism):** Identical input state and policy records always yield identical scoring and policy outputs.

# RecoverX: Deterministic Policy & Guard Engine Specification

**Product:** RecoverX  
**Module:** `PolicyEngine`  
**Policy Version:** `v1`  
**Guiding Invariant:** *The policy engine has zero tolerance for hallucination, race conditions, or financial overreach.*

---

## 1. Decision Semantics: `ALLOW` vs `BLOCK` vs `ESCALATE`

Every proposed recovery action evaluated by `PolicyEngine` yields exactly one of three deterministic decisions:

| Decision | Meaning | Execution Consequence |
| :--- | :--- | :--- |
| **`ALLOW`** | All deterministic safety rules, spending caps, cooldowns, and status guards passed. | Autonomous execution is permitted to dispatch the authorized action. |
| **`BLOCK`** | The proposed action is unsafe, impossible, redundant, or strictly disallowed (e.g. order is already paid, action not allowlisted, duplicate active action). | Action execution is halted completely; opportunity state is NOT escalated to human queue. |
| **`ESCALATE`** | The opportunity represents recoverable revenue, but exceeds autonomous spending thresholds or retry caps (e.g. high-ticket amount > ₹15,000, max retries exhausted). | Action execution is paused; opportunity status transitions to `ESCALATED` for merchant dashboard review. |

---

## 2. Rule Evaluation Hierarchy & Safety Invariants

Rules are evaluated sequentially. A single blocking rule terminates evaluation and returns the definitive decision.

```
Incoming Proposed Action + Context
       │
       ▼
[1. Order Paid Guard] ───────────────► If Order == PAID ──────────────► BLOCK ("ORDER_ALREADY_PAID")
       │
       ▼
[2. Terminal State Guard] ───────────► If Opportunity in (RECOVERED, ──► BLOCK ("OPPORTUNITY_TERMINAL")
       │                                                 CLOSED)
       ▼
[3. Action Allowlist Guard] ─────────► If Action not in AllowedActions ─► BLOCK ("ACTION_NOT_ALLOWED")
       │
       ▼
[4. Duplicate Action Guard] ─────────► If Identical Action Dispatched ──► BLOCK ("DUPLICATE_ACTION_EXISTS")
       │
       ▼
[5. Auto-Recovery Enabled Guard] ────► If Policy.AutoRecovery == False ─► ESCALATE ("AUTO_RECOVERY_DISABLED")
       │
       ▼
[6. Max Retry Limit Guard] ──────────► If AttemptCount >= MaxRetries ──► ESCALATE ("MAX_RETRIES_EXCEEDED")
       │
       ▼
[7. Amount Spending Cap Guard] ──────► If Amount > MaxAutoRecoveryCap ──► ESCALATE ("AMOUNT_EXCEEDS_CAP")
       │
       ▼
[8. Cooldown Interval Guard] ────────► If Now < LastAttempt + Cooldown ─► BLOCK ("COOLDOWN_ACTIVE")
       │
       ▼
[9. ALL GUARDS PASSED] ────────────────────────────────────────────────► ALLOW ("POLICY_APPROVED")
```

---

## 3. The 10 Invariant Truths

1. **INVARIANT 1 (Paid Order Isolation):** A paid order can NEVER receive recovery approval under any circumstance.
2. **INVARIANT 2 (Terminal Opportunity Seal):** An opportunity marked `RECOVERED` or `CLOSED_UNRECOVERED` cannot be reopened by an automated action.
3. **INVARIANT 3 (Retry Cap Enforcement):** Total autonomous attempts cannot exceed `merchant_policies.max_retry_attempts`.
4. **INVARIANT 4 (Financial Limit Protection):** No action on an order exceeding `merchant_policies.max_auto_recovery_amount_inr` may execute without human approval.
5. **INVARIANT 5 (Strict Allowlist Control):** An action type outside `merchant_policies.allowed_actions` is rejected instantly.
6. **INVARIANT 6 (Cooldown Protection):** Automated contacts must honor `merchant_policies.cooldown_minutes` between attempts.
7. **INVARIANT 7 (Merchant Kill-Switch):** Toggling `auto_recovery_enabled = False` immediately halts all automated approvals across the merchant.
8. **INVARIANT 8 (Immutable Policy Versioning):** Every policy decision records the active `policy_version` (`v1`) alongside machine-readable reason codes.
9. **INVARIANT 9 (Machine-Readable Explainability):** All decisions contain structured `reason_codes` and human-readable explanation strings.
10. **INVARIANT 10 (100% Determinism):** Identical input state and policy records always yield identical scoring and policy outputs.

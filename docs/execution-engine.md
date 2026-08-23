# RecoverX Execution Engine Specification

**Product:** RecoverX  
**Module:** `ActionExecutorService` & `PaymentGatewayAdapter`  
**Execution Invariant:** *Zero untrusted financial execution. 100% of payment operations are strictly gated by the Policy Engine and executed via deterministic idempotency keys.*

---

## 1. Execution State Machine

```
[PENDING]
    │
    ▼
[QUEUED] ────────► Enqueued with deterministic idempotency key
    │
    ▼
[EXECUTING] ─────► Pre-execution safety check passed; DB transaction committed
    │
    ├─────────────────────────────┬─────────────────────────────┐
    ▼                             ▼                             ▼
[SUCCEEDED]                   [FAILED]                     [AMBIGUOUS]
(Payment Link Created)    (Validation / 4xx error)    (Network timeout / 5xx)
                                                            │
                                                            ▼
                                                Reconcile before retry
```

---

## 2. Pre-Execution Safety Checks

Before dispatching an external request to Razorpay, the executor transactionally verifies:
1. **Order Unpaid:** If `order.status == PAID`, action transitions immediately to `CANCELLED` (`ORDER_ALREADY_PAID`).
2. **Opportunity Active:** If `opportunity.status` is `RECOVERED` or `CLOSED_UNRECOVERED`, action transitions to `CANCELLED`.
3. **Policy Limits:** Spending caps, maximum retries, and cooldown intervals are verified against current database state.
4. **Authoritative Amount:** The amount is calculated strictly from `order.amount_inr` on the server. The AI agent or frontend cannot modify the amount.

---

## 3. Idempotency Key Design

* Format: `recovery:{opportunity_id}:attempt:{attempt_number}`
* Uniqueness enforced at the PostgreSQL database level (`UNIQUE(idempotency_key)` on `recovery_actions`).
* Re-executing an already `SUCCEEDED` or `CANCELLED` action returns immediately without calling the gateway.

---

## 4. Ambiguity Handling & Safe Retries

* **Timeout Handling:** If an HTTP timeout occurs, the action transitions to `AMBIGUOUS` (not `FAILED`).
* **No Blind Retries:** The system refuses to create a second payment link until provider state is reconciled.

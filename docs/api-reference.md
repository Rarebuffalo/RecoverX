# RecoverX API Reference

This document outlines all live REST endpoints exposed by the RecoverX FastAPI backend (`/api/v1`).

---

## 1. System Health & Infrastructure

### `GET /health`
* **Purpose:** Liveness probe verifying the API server is up and responsive.
* **Request:** None
* **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "environment": "development"
  }
  ```

### `GET /ready`
* **Purpose:** Readiness probe verifying PostgreSQL and Redis connections and latencies.
* **Request:** None
* **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "database": { "status": "ok", "latency_ms": 1.2 },
    "redis": { "status": "ok", "latency_ms": 0.8 }
  }
  ```

### `GET|POST /api/v1/agent/checkin` & `GET|POST /api/v1/agent/heartbeat`
* **Purpose:** Daemon liveness and heartbeat checks for IDE / background worker monitoring.
* **Query Params:** `device_id` (optional string)
* **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "device_id": "73e9facf-...",
    "message": "RecoverX agent checkin acknowledged."
  }
  ```

---

## 2. Recovery Opportunities & Work Queue

### `GET /api/v1/opportunities`
* **Purpose:** Lists all detected recovery opportunities with associated orders, customer metadata, and payment attempts.
* **Response (200 OK):** Array of `RecoveryOpportunity` objects.

### `GET /api/v1/opportunities/{opportunity_id}`
* **Purpose:** Retrieves full opportunity detail. Accepts UUIDs or canonical demo string aliases (`opp_demo_01` through `opp_demo_04`).
* **Response (200 OK):** `RecoveryOpportunity` object with nested order, customer, and payment attempts.
* **Errors:** `404 Not Found` if opportunity does not exist.

### `POST /api/v1/opportunities/{opportunity_id}/agent-evaluate`
* **Purpose:** Dispatches sanitized failure context to the AI Diagnostic Agent (`recovery-diagnostic-v1`) to generate an advisory proposal.
* **Response (200 OK):**
  ```json
  {
    "opportunity_id": "opp_demo_01",
    "proposal": {
      "diagnosis_category": "TRANSIENT_PAYMENT_FAILURE",
      "diagnosis_summary": "NPCI switch timeout during UPI authorization. Low customer friction risk.",
      "recommended_action": "CREATE_RECOVERY_PAYMENT_LINK",
      "confidence": 0.94,
      "fallback_action": "ESCALATE_TO_MERCHANT",
      "decision_factors": ["High customer lifetime value", "First attempt failure", "Payment gateway timeout code"]
    },
    "provider": "mock",
    "evaluated_at": "2026-09-04T00:00:00Z"
  }
  ```

### `POST /api/v1/opportunities/{opportunity_id}/execute`
* **Purpose:** Evaluates deterministic Policy Gate rules and dispatches bounded financial action (e.g. Razorpay Payment Link) if allowed.
* **Response (200 OK):**
  ```json
  {
    "action_id": "act_...",
    "opportunity_id": "opp_demo_01",
    "action_type": "CREATE_RECOVERY_PAYMENT_LINK",
    "execution_status": "SUCCEEDED",
    "payment_link_url": "https://rzp.io/i/rec_mock_...",
    "idempotency_key": "recovery:opp_demo_01:attempt:1"
  }
  ```
* **Errors:** `400 Bad Request` if order is already paid or terminal state reached.

---

## 3. Actions Ledger & Audit Trail

### `GET /api/v1/actions`
* **Purpose:** Lists all dispatched payment links, retries, and gateway executions.
* **Response (200 OK):** Array of `RecoveryAction` records.

### `GET /api/v1/audit-events`
* **Purpose:** Returns the append-only cryptographic audit ledger of all domain events, policy decisions, and webhook settlements.
* **Response (200 OK):** Array of `AuditEvent` objects.

---

## 4. Policy Configuration

### `GET /api/v1/policies`
* **Purpose:** Retrieves active configurable policy parameters alongside the 10 immutable safety invariants.
* **Response (200 OK):**
  ```json
  {
    "rules": [
      { "id": "max_recovery_amount", "name": "Maximum Autonomous Recovery Amount", "value": 15000, "unit": "INR" },
      { "id": "min_recovery_score", "name": "Minimum Score for Auto-Recovery", "value": 60, "unit": "points" },
      { "id": "max_recovery_attempts", "name": "Maximum Recovery Attempts per Order", "value": 2, "unit": "attempts" },
      { "id": "cooldown_period_minutes", "name": "Cooldown Period Between Attempts", "value": 30, "unit": "minutes" }
    ],
    "immutable_invariants": [
      "No recovery on paid orders",
      "No recovery on cancelled/refunded orders",
      "Deterministic idempotency on payment creation",
      "Cryptographic HMAC verification on all webhooks"
    ]
  }
  ```

### `PUT /api/v1/policies`
* **Purpose:** Updates configurable policy thresholds (e.g. maximum autonomous amount cap or score threshold).
* **Request Body:**
  ```json
  {
    "max_recovery_amount": 20000,
    "min_recovery_score": 65,
    "max_recovery_attempts": 2,
    "cooldown_period_minutes": 30
  }
  ```

---

## 5. Webhook Ingestion

### `POST /api/v1/webhooks/razorpay`
* **Purpose:** Ingests live Razorpay payment, order, and payment link webhooks.
* **Headers Required:** `X-Razorpay-Signature`, `X-Razorpay-Event-Id` (optional)
* **Supported Events:**
  - `payment.failed` (Initializes `RecoveryOpportunity` in `DETECTED` status)
  - `payment.captured` (Reconciles order and transitions opportunity to `RECOVERED`)
  - `order.paid` (Transitions order and prevents any future recovery attempts)
  - `payment_link.paid` (Reconciles dispatched payment link and settles recovered revenue)
* **Response (200 OK):**
  ```json
  {
    "status": "processed",
    "event_id": "evt_...",
    "event_type": "payment_link.paid",
    "message": "Event successfully processed and synchronized."
  }
  ```
* **Errors:**
  - `401 Unauthorized`: Missing or invalid HMAC-SHA256 signature.
  - `400 Bad Request`: Empty body or malformed JSON payload.

---

## 6. Developer & Demo Utilities

> **Note:** These endpoints are reserved for local evaluation, pitch demonstrations, and test harness execution.

### `POST /api/v1/developer/reset-demo-state`
* **Purpose:** Restores database opportunities, orders, and action ledgers to a clean pre-recovery baseline state.
* **Response (200 OK):** `{"status": "reset_completed", "message": "Demo environment state reset to clean baseline."}`

### `POST /api/v1/developer/simulate-payment-success`
* **Purpose:** Synthesizes and ingests an authentic `payment_link.paid` webhook for a target opportunity to simulate payment capture without external network calls.
* **Request Body:** `{"opportunity_id": "opp_demo_01"}`
* **Response (200 OK):**
  ```json
  {
    "status": "simulated_success",
    "opportunity_id": "opp_demo_01",
    "recovered_amount_inr": 8499.0
  }
  ```

### `GET /api/v1/analytics/benchmark`
* **Purpose:** Returns the Phase 7A 25,000 synthetic transaction benchmark results and threshold frontier.

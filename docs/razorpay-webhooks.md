# Razorpay Webhook Ingestion & Synchronization Specification

**Product:** RecoverX  
**Status:** Verified for Phase 2 Implementation  
**Reference:** Official Razorpay API & Webhook Technical Specifications

---

## 1. Webhook Signature & Header Verification

### 1.1 Headers
* **Signature Header:** `X-Razorpay-Signature` (case-insensitive in HTTP/1.1 & HTTP/2).
* **Event ID Header (Optional):** `X-Razorpay-Event-Id`.

### 1.2 Signature Algorithm (HMAC-SHA256)
Razorpay computes HMAC-SHA256 over the **exact raw HTTP request body bytes** using the merchant's configured Webhook Secret.
$$\text{Expected Signature} = \text{HMAC\_SHA256}(\text{raw\_request\_body\_bytes}, \text{webhook\_secret})$$

* **Verification Rules:**
  1. The raw bytes must be captured before any JSON parsing, whitespace transformation, or deserialization.
  2. The signature comparison MUST use constant-time comparison (`hmac.compare_digest`) to prevent timing side-channel attacks.
  3. If `X-Razorpay-Signature` is missing or does not match, the server returns `HTTP 401 Unauthorized` without executing downstream business logic.
  4. Webhook secrets and full signatures are NEVER logged.

---

## 2. Supported Events & Payload Mappings

Razorpay represents monetary amounts in **subunits (paise)** (e.g. `499900` paise = `₹4,999.00`). RecoverX canonicalizes all amounts to `INR` (`Decimal(amount / 100)`).

### 2.1 `payment.failed`
* **Purpose:** Emitted when a customer checkout or charge attempt fails.
* **Payload Path:** `payload.payment.entity`
* **Key Fields Used:**
  - `id`: `pay_xxx` (Provider Payment ID)
  - `order_id`: `order_xxx` (Provider Order ID)
  - `amount`: Integer in paise (e.g. `849900` $\rightarrow$ `8499.00 INR`)
  - `currency`: `INR`
  - `method`: `upi`, `card`, `netbanking`, `wallet`, `emi`
  - `error_code`: String (e.g. `BAD_REQUEST_GATEWAY_TIMEOUT`, `PAYMENT_CARD_INSUFFICIENT_FUNDS`)
  - `error_description`: Text explanation from bank/gateway
  - `email` & `contact`: Customer contact identifiers
* **RecoverX Mapping:**
  - Locate or initialize canonical `Order` for `order_id`.
  - Upsert `PaymentAttempt` with status `failed`, failure code, and failure reason.
  - If the order is NOT already `paid`, create `RecoveryOpportunity` in state `DETECTED`.
  - Record `audit_event`.

### 2.2 `payment.captured`
* **Purpose:** Emitted when a payment is authorized and captured successfully.
* **Payload Path:** `payload.payment.entity`
* **Key Fields Used:**
  - `id`: `pay_xxx`
  - `order_id`: `order_xxx`
  - `amount`: Integer in paise
  - `status`: `captured`
* **RecoverX Mapping:**
  - Locate `Order` and upsert `PaymentAttempt` with status `captured`.
  - Transition `Order` status to `paid`.
  - **Recovery Preemption:** If an active `RecoveryOpportunity` exists for this order, transition it immediately to `RECOVERED` with `recovered_amount_inr = order.amount_inr`.
  - Record `audit_event`.

### 2.3 `order.paid`
* **Purpose:** Emitted when an order is completely paid (reconciliation event).
* **Payload Path:** `payload.order.entity`
* **Key Fields Used:**
  - `id`: `order_xxx`
  - `amount_paid`: Integer in paise
  - `status`: `paid`
* **RecoverX Mapping:**
  - Verify and set `Order` status to `paid`.
  - If a `RecoveryOpportunity` exists in a non-terminal state, mark it `RECOVERED`.
  - Record `audit_event`.

### 2.4 `payment_link.paid`
* **Purpose:** Emitted when a customer completes payment via a generated Razorpay Payment Link.
* **Payload Path:** `payload.payment_link.entity` (and contains `payload.payment.entity`)
* **Key Fields Used:**
  - `id`: `plink_xxx` (Payment Link ID)
  - `order_id`: `order_xxx` (or `reference_id` linking back to order)
  - `amount_paid`: Integer in paise
  - `status`: `paid`
* **RecoverX Mapping:**
  - Update matching `RecoveryAction` provider reference.
  - Transition `Order` status to `paid` and `RecoveryOpportunity` to `RECOVERED`.
  - Record `audit_event`.

---

## 3. Idempotency & Webhook Deduplication Strategy

To guarantee that duplicate webhooks never produce duplicate business mutations:

1. **Unique Deduplication Key:** `(provider, event_id)`.
2. **Atomic Registration:**
   ```sql
   INSERT INTO processed_webhooks (provider, event_id, event_type, payload, processed_at)
   VALUES ('razorpay', :event_id, :event_type, :payload, NOW())
   ON CONFLICT (provider, event_id) DO NOTHING;
   ```
3. **Branching Logic:**
   - **If row inserted (1):** Event is fresh $\rightarrow$ Process business synchronization $\rightarrow$ Return `HTTP 200 OK {"status": "processed"}`.
   - **If row conflict (0):** Event is a duplicate $\rightarrow$ Return `HTTP 200 OK {"status": "already_processed"}` $\rightarrow$ Skip business processing.

---

## 4. Event Ordering & Convergence Precedence

Because network delivery is asynchronous, webhooks may arrive out of order (e.g. `payment.captured` arriving before a delayed `payment.failed` retry).

### State Precedence Matrix:
$$\text{PAID / CAPTURED} \succ \text{ATTEMPTED / FAILED} \succ \text{CREATED}$$

1. **Terminal Capture Dominance:** Once an order is marked `paid` or an opportunity is marked `RECOVERED`, a subsequent `payment.failed` event for an older attempt will record the payment attempt as failed, but will **NEVER revert the order to unpaid or reopen the recovery opportunity**.
2. **Row-Level Concurrency Locks:** State transitions on orders and recovery opportunities acquire `SELECT ... FOR UPDATE` row locks within the active database transaction to prevent concurrent race conditions.

---

## 5. Architectural Tradeoff: Direct Async Service vs. Outbox Pattern

* **Phase 2 Choice:** Atomic `processed_webhooks` registration followed by transactional domain synchronization inside the service worker boundary.
* **Why this is optimal for MVP:** PostgreSQL ACID guarantees ensure that the idempotency check, payment attempt upsert, order update, and audit log write occur within an atomic database transaction. If the transaction rolls back, the webhook is not acknowledged as processed, prompting Razorpay to retry safely.

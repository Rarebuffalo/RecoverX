# Razorpay Payment Links API Specification & Integration Guide

**Product:** RecoverX  
**API Track:** Razorpay Standard Payment Links v1  
**Integration Status:** Verified & Bounded

---

## 1. Official Razorpay Payment Links Specification

### 1.1 Endpoint & Method
* **Endpoint:** `POST https://api.razorpay.com/v1/payment_links/`
* **Authentication:** HTTP Basic Authentication using `RAZORPAY_KEY_ID:RAZORPAY_KEY_SECRET`.
* **Content-Type:** `application/json`

### 1.2 Request Payload Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `amount` | `integer` | **Yes** | Amount in **currency sub-units** (paise for INR). Example: `₹8,499.00` &rarr; `849900`. |
| `currency` | `string` | **Yes** | 3-letter ISO code. Default: `"INR"`. |
| `accept_partial` | `boolean` | Optional | Set to `false` (default) for exact invoice payments. |
| `reference_id` | `string` | **Yes** | Merchant internal unique idempotency reference. Format: `rec_act_<uuid>`. |
| `description` | `string` | **Yes** | Human-readable explanation. Example: `"RecoverX: Recovery Payment for Order #order_01"`. |
| `customer` | `object` | Optional | Object containing `name`, `email`, `contact`. |
| `expire_by` | `integer` | Optional | Unix timestamp for link expiration (e.g. `now + 48 hours`). |
| `reminder_enable`| `boolean` | Optional | `false` (RecoverX manages its own recovery cadences). |
| `notes` | `object` | Optional | Key-value pairs for metadata (`opportunity_id`, `merchant_id`, `action_id`). |

### 1.3 Response Payload Structure
```json
{
  "id": "plink_Qwert123456789",
  "accept_partial": false,
  "amount": 849900,
  "amount_paid": 0,
  "cancelled_at": 0,
  "created_at": 1771678800,
  "currency": "INR",
  "customer": {
    "contact": "+919876543210",
    "email": "customer@example.com",
    "name": "Customer Name"
  },
  "description": "RecoverX: Recovery Payment for Order #order_01",
  "expire_by": 1771851600,
  "expired_at": 0,
  "first_min_partial_amount": 0,
  "notes": {
    "action_id": "99999999-9999-9999-9999-999999999999",
    "opportunity_id": "44444444-4444-4444-4444-444444444441"
  },
  "order_id": "order_Qwert123456789",
  "reference_id": "rec_act_99999999",
  "reminder_enable": false,
  "reminders": [],
  "short_url": "https://rzp.io/i/Xyz123",
  "status": "created",
  "updated_at": 1771678800,
  "user_id": ""
}
```

### 1.4 Associated Webhook Events
* `payment_link.paid`: Dispatched when the customer completes payment through the payment link.
* `payment.captured`: Dispatched when the underlying payment is successfully captured.
* `payment_link.expired`: Dispatched if the payment link reaches `expire_by` without completion.
* `payment_link.cancelled`: Dispatched if canceled manually.

---

## 2. Invariant Integration Rules in RecoverX

1. **Amount Integrity:** `amount` is ALWAYS computed on the backend server from `orders.amount_inr` multiplied by 100. The AI agent or client frontend has **zero** control over the monetary amount.
2. **Idempotency Keying:** Every action creates a deterministic `reference_id` (`recovery:{opportunity_id}:attempt:{attempt_number}`).
3. **Dual Gateway Adapters:**
   - `LocalDeterministicMockAdapter`: Offline, reproducible deterministic mock generating synthetic URLs and provider action IDs without network calls.
   - `RazorpaySandboxAdapter`: Real HTTP calls to `https://api.razorpay.com/v1/payment_links/` in Test Mode.

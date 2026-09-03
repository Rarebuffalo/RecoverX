# RecoverX Manual Testing Guide & Demo Procedures

This guide provides end-to-end verification instructions for both **Mode 1 (Local Deterministic Demo)** and **Mode 2 (Real Razorpay Test Mode)**.

---

## Part 1: Mode 1 — Local Deterministic Demo Testing

Mode 1 requires zero external credentials or internet connectivity. It uses the `LocalDeterministicMockAdapter` and `LocalDeterministicMockLLM`.

### Hero Test: Scenario A (Safe Recovery — ₹8,499)
1. **Reset Demo State:**
   - Navigate to **Demo Center** (`/dashboard/demo`) or run:
     ```bash
     curl -X POST http://localhost:8000/api/v1/developer/reset-demo-state
     ```
2. **Open Opportunity Inspector:**
   - Navigate to `/opportunities/opp_demo_01`.
   - Verify failure diagnosis: `Bank NPCI switch timed out during UPI authorization`.
3. **Trigger AI Reasoning:**
   - Click **Run AI Evaluation**.
   - Verify advisory proposal: `CREATE_RECOVERY_PAYMENT_LINK` (Confidence: 94%).
4. **Verify Deterministic Policy Gate:**
   - Observe deterministic score: `87/100 (HIGH)`.
   - Verify policy authority verdict: **`ALLOW`**.
5. **Dispatch Payment Link:**
   - Click **Generate Recovery Link**.
   - Verify link generated: `https://rzp.io/i/rec_mock_opp_demo_01` with state `INTERVENED`.
6. **Simulate Customer Payment:**
   - Click **Simulate Customer Payment**.
   - Verify state transitions to **`RECOVERED` (₹8,499)**.
7. **Verify Platform Consistency:**
   - Navigate to **Command Center** (`/dashboard`): Recovered revenue increases by ₹8,499.
   - Navigate to **Actions Ledger** (`/dashboard/actions`): Execution status is `SUCCESS`.
   - Navigate to **Audit Ledger** (`/dashboard/audit`): `PAYMENT_LINK_PAID_PROCESSED` event recorded.

---

## Part 2: Safety & Policy Invariant Tests

### Test 2: Scenario B — Policy Escalation (₹45,000 High Ticket)
* **Goal:** Verify policy prevents autonomous action when order value exceeds merchant cap (₹15,000).
* **Steps:** Open `/opportunities/opp_demo_02`.
* **Expected Result:**
  - AI may propose link or review.
  - Policy Gate verdict is **`ESCALATE`** (`REVENUE_EXCEEDS_AUTONOMOUS_LIMIT`).
  - **No automated action CTA exists**. Marked as `MANUAL_REVIEW_REQUIRED`.

### Test 3: Scenario D — Ambiguous Gateway Timeout (₹3,250)
* **Goal:** Verify platform holds action rather than blindly retrying when payment state is indeterminate.
* **Steps:** Open `/opportunities/opp_demo_04`.
* **Expected Result:**
  - Status is **`AMBIGUOUS / HELD`**.
  - System blocks blind retry until payment switch reconciliation occurs.

### Test 4: Scenario E — Hard Block / Stolen Card (₹6,500)
* **Goal:** Verify hard fraud/stolen card declines are permanently blocked.
* **Steps:** Open `/opportunities/opp_demo_03`.
* **Expected Result:**
  - Score is `< 20/100`.
  - Policy Gate verdict is **`BLOCK`** (`PERMANENT_DECLINE_DETECTED`).
  - Opportunity is closed without execution.

---

## Part 3: Mode 2 — Real Razorpay Test Mode Demonstration

Mode 2 connects RecoverX directly to the Razorpay Test Mode API and receives authentic webhooks.

### Prerequisites
1. **Razorpay Dashboard Account** with Test Mode active (`rzp_test_...`).
2. **Environment Configuration:**
   In `.env`:
   ```bash
   EXECUTION_MODE=razorpay_sandbox
   RAZORPAY_KEY_ID=rzp_test_YourKeyIdHere
   RAZORPAY_KEY_SECRET=YourKeySecretHere
   RAZORPAY_WEBHOOK_SECRET=YourWebhookSecretHere
   ```
3. **Public HTTPS Tunnel for Webhook Ingestion:**
   Expose local port `8000`:
   ```bash
   ngrok http 8000
   # OR: zrok share public http://localhost:8000
   ```
4. **Configure Razorpay Webhook:**
   - In Razorpay Dashboard &rarr; Settings &rarr; Webhooks &rarr; Add New Webhook.
   - **URL:** `https://<your-tunnel-subdomain>/api/v1/webhooks/razorpay`
   - **Secret:** Must match `RAZORPAY_WEBHOOK_SECRET`.
   - **Active Events:** Check `payment_link.paid`, `payment.failed`, `payment.captured`.

### Real Test Execution Steps
1. Open `/opportunities/opp_demo_01`.
2. Click **Generate Recovery Link**.
   - RecoverX calls `POST https://api.razorpay.com/v1/payment_links` using your test credentials.
   - An authentic Razorpay test short link (e.g. `https://rzp.io/i/abc123xyz`) is generated.
3. Open the generated Payment Link in a browser.
4. Complete a test payment using standard Razorpay Test Cards / UPI simulation.
5. Razorpay delivers an HMAC-signed `payment_link.paid` event to your webhook URL.
6. RecoverX verifies the HMAC-SHA256 signature, resolves the opportunity, and transitions status to **`RECOVERED`**.
7. Refresh Command Center to see verified real test recovered revenue.

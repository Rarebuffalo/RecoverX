# RecoverX Outcome & Settlement Engine Specification

**Product:** RecoverX  
**Module:** `RecoveryOutcomeService`  
**Core Thesis:** *Payment link creation is NOT recovery. Recovered revenue requires verified proof of a captured payment matching the recovery order.*

---

## 1. The Verification & Causality Standard

Recovered revenue is recognized **only** when all of the following criteria are satisfied:
1. **Verified Payment Event:** A valid `payment.captured` or `payment_link.paid` webhook event is processed through HMAC-SHA256 signature verification.
2. **Order Reconciliation:** The payment entity's `order_id` or `payment_link.order_id` corresponds to the authoritative RecoverX `orders.id`.
3. **Double-Counting Prevention:** If the opportunity is already in `RECOVERED` state, duplicate webhooks are ignored without inflating recovered revenue.

---

## 2. Amount Reconciliation Logic

* **Full Recovery:** `amount_captured >= revenue_at_risk` &rarr; `status = RECOVERED`, `recovered_amount_inr = amount_captured`.
* **Partial Recovery:** `amount_captured < revenue_at_risk` &rarr; `status = PARTIALLY_RECOVERED`, `recovered_amount_inr += amount_captured`.
* **Overpayment:** `amount_captured > revenue_at_risk` &rarr; `status = RECOVERED`, `recovered_amount_inr = amount_captured`.

---

## 3. Recovery Metrics Formulas

$$\text{Revenue at Risk} = \sum_{\text{unresolved opps}} \text{revenue\_at\_risk\_inr}$$

$$\text{Recovered Revenue} = \sum_{\text{all opps}} \text{recovered\_amount\_inr}$$

$$\text{Recovery Rate} = \frac{\text{Total Recovered Revenue}}{\text{Total Revenue at Risk} + \text{Total Recovered Revenue}}$$

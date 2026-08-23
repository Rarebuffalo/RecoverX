# RecoverX: Interpretable Recovery Scoring Specification

**Product:** RecoverX  
**Module:** `RecoveryScoringService` & `FailureClassifier`  
**Status:** Deterministic / Zero-Blackbox Rule Specification

---

## 1. Core Philosophy: Interpretable Feature Contributions

Unlike black-box machine learning models, RecoverX's MVP scoring engine uses a **fully inspectable additive feature scoring model**. Every single point in the $0 - 100$ score is mathematically accounted for by explicit signal weights.

$$\text{Final Recovery Score} = \text{clamp}\left(\sum \text{Feature Points}, \ 0, \ 100\right)$$

---

## 2. Failure Classification Rules (`FailureClassifier`)

Razorpay failure codes and descriptions are mapped deterministically into normalized recovery categories:

| Normalized Category | Triggering Error Codes / Keywords | Base Points | Recovery Profile |
| :--- | :--- | :---: | :--- |
| **`TRANSIENT`** | `GATEWAY_TIMEOUT`, `NETWORK_ERROR`, `BANK_SWITCH_DOWN`, `INTERNAL_SERVER_ERROR`, `AUTH_TIMEOUT` | **+30** | Temporary gateway/bank infrastructure glitches. Highest probability of immediate success via retry/link. |
| **`CUSTOMER_ACTION_REQUIRED`** | `USER_CANCELLED`, `OTP_EXPIRED`, `3DS_DROPPED`, `APP_CLOSED`, `WINDOW_CLOSED` | **+20** | User abandoned checkout drawer or OTP prompt. Highly recoverable via direct payment link. |
| **`INSUFFICIENT_FUNDS`** | `INSUFFICIENT_FUNDS`, `ACCOUNT_BALANCE_LOW`, `CREDIT_LIMIT_EXCEEDED` | **+10** | Immediate retry will fail. Requires cooldown or customer wallet top-up. |
| **`PAYMENT_METHOD_ISSUE`** | `INVALID_CVV`, `CARD_EXPIRED`, `INVALID_PIN`, `VPA_NOT_FOUND`, `DAILY_LIMIT_EXCEEDED` | **+5** | Method-specific error. Recoverable only if customer chooses an alternative payment method. |
| **`PERMANENT`** | `CARD_STOLEN`, `CARD_BLOCKED`, `ACCOUNT_FROZEN`, `FRAUD_SUSPECTED`, `BANK_BLACKLIST` | **-40** | Hard decline. Severe risk of chargeback or regulatory flag. Non-recoverable. |
| **`UNKNOWN`** | Any unmapped or missing error code | **+0** | Conservative neutral baseline. |

---

## 3. Interpretable Feature Scoring Weights

The total score starts at a neutral baseline of **30 points** and accumulates additive feature adjustments:

### 3.1 Failure Category Signal ($\pm 40$ pts)
- Derived directly from `FailureClassifier` base points.

### 3.2 Customer Historical Payment Reliability ($\pm 25$ pts)
- **High Success Rate ($\ge 80\%$ with $\ge 3$ prior orders):** **+25 pts**
- **Moderate Success Rate ($50\% - 79\%$):** **+15 pts**
- **New Customer ($0$ previous orders):** **+5 pts** (Neutral)
- **Chronic Failure Customer ($< 30\%$ success with $\ge 3$ orders):** **-15 pts**

### 3.3 Historical Lifetime Value (LTV) ($\pm 15$ pts)
- **High LTV ($\ge \text{₹20,000}$):** **+15 pts**
- **Mid LTV ($\text{₹5,000} - \text{₹19,999}$):** **+10 pts**
- **Low / Zero LTV ($< \text{₹5,000}$):** **+0 pts**

### 3.4 Recovery Attempt Degradation Penalty ($-15$ pts per attempt)
- **0 prior attempts:** **+10 pts** (Fresh failure)
- **1 prior attempt:** **-10 pts** (Diminishing return)
- **2+ prior attempts:** **-25 pts** (Exhaustion risk)

### 3.5 Transaction Value Risk Factor ($\pm 10$ pts)
- **Low Ticket ($< \text{₹5,000}$):** **+10 pts** (Impulse recovery high)
- **Mid Ticket ($\text{₹5,000} - \text{₹20,000}$):** **+5 pts**
- **High Ticket ($> \text{₹20,000}$):** **-10 pts** (Higher fraud & affordability friction)

### 3.6 Recency Factor ($\pm 10$ pts)
- **Fresh ($< 30$ mins):** **+10 pts**
- **Recent ($30 - 120$ mins):** **+5 pts**
- **Stale ($> 24$ hours):** **-15 pts**

---

## 4. Configurable Score Bands

| Score Band | Range | Recommended Action Strategy | Default Operational Route |
| :--- | :---: | :--- | :--- |
| **`HIGH`** | $80 - 100$ | Immediate Payment Link Dispatch | `AUTO_RECOVER` |
| **`MEDIUM`** | $60 - 79$ | Cooldown Delayed Link / Reminder | `AUTO_RECOVER` |
| **`LOW`** | $40 - 59$ | Requires Merchant Review / Custom Incentive | `MANUAL_REVIEW` |
| **`VERY_LOW`** | $0 - 39$ | Do Not Intervene (High friction / hard decline) | `DO_NOT_RECOVER` |

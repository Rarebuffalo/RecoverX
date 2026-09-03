# Deploying RecoverX to Railway

This guide describes how to deploy RecoverX to [Railway](https://railway.app/) for a public, cloud-hosted demonstration with real Razorpay Test Mode integration.

---

## 1. High-Level Architecture on Railway

```
                                ┌───────────────────────────┐
                                │      Railway Project      │
                                │                           │
User Browser ──────────────────►│ Service: recoverx-web     │ (Next.js 14)
                                │       │                   │
                                │       ▼                   │
Razorpay Test Rails ───────────►│ Service: recoverx-api     │ (FastAPI)
(Payment Links & Webhooks)      │   │          │            │
                                │   │          ▼            │
                                │   │    Railway Redis      │
                                │   │          ▲            │
                                │   │          │            │
                                │   │    recoverx-worker    │ (Celery)
                                │   ▼                       │
                                │ Railway PostgreSQL        │
                                └───────────────────────────┘
```

---

## 2. Prerequisites
1. A **Railway Account** ([railway.app](https://railway.app/)).
2. A **Razorpay Test Account** ([dashboard.razorpay.com](https://dashboard.razorpay.com/)) with Test Mode active.

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Create a Railway Project & Databases
1. Log in to Railway and click **New Project** &rarr; **Provision PostgreSQL**.
2. In the same project canvas, click **+ New** &rarr; **Database** &rarr; **Redis**.

---

### Step 2: Deploy Backend API (`recoverx-api`)
1. Click **+ New** &rarr; **GitHub Repo** &rarr; Select `RecoverX`.
2. In the service settings:
   - **Service Name:** `recoverx-api`
   - **Root Directory:** `/apps/api`
   - **Dockerfile Path:** `Dockerfile` (or root default)
3. Navigate to **Variables** and configure:

| Variable | Recommended Value / Reference | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Connects to Railway PostgreSQL |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Connects to Railway Redis |
| `ENVIRONMENT` | `production` | Production mode flag |
| `EXECUTION_MODE` | `razorpay_sandbox` (or `local_deterministic`) | Selects gateway execution adapter |
| `RAZORPAY_KEY_ID` | `rzp_test_...` | Razorpay Test API Key ID |
| `RAZORPAY_KEY_SECRET` | `••••••••••••` *(Secret)* | Razorpay Test API Key Secret |
| `RAZORPAY_WEBHOOK_SECRET` | `••••••••••••` *(Secret)* | Secret string for HMAC verification |
| `LLM_PROVIDER` | `mock` (or `gemini`) | AI diagnostic reasoning engine |
| `LLM_API_KEY` | *(Optional)* | Google Gemini API Key if using `gemini` |
| `CORS_ORIGINS` | `https://${{recoverx-web.RAILWAY_PUBLIC_DOMAIN}},http://localhost:3000` | Allowed origins |

4. Navigate to **Settings** &rarr; **Networking** &rarr; Click **Generate Domain** (e.g. `recoverx-api-production.up.railway.app`).

---

### Step 3: Deploy Celery Background Worker (`recoverx-worker`)
1. Click **+ New** &rarr; **GitHub Repo** &rarr; Select `RecoverX`.
2. In the service settings:
   - **Service Name:** `recoverx-worker`
   - **Root Directory:** `/apps/api`
   - **Custom Start Command:**
     ```bash
     celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=2
     ```
3. In **Variables**, add:
   - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
   - `REDIS_URL`: `${{Redis.REDIS_URL}}`
   - `EXECUTION_MODE`: `razorpay_sandbox` (or `local_deterministic`)
   - `RAZORPAY_KEY_ID`: `${{recoverx-api.RAZORPAY_KEY_ID}}`
   - `RAZORPAY_KEY_SECRET`: `${{recoverx-api.RAZORPAY_KEY_SECRET}}`

---

### Step 4: Deploy Frontend Web Dashboard (`recoverx-web`)
1. Click **+ New** &rarr; **GitHub Repo** &rarr; Select `RecoverX`.
2. In the service settings:
   - **Service Name:** `recoverx-web`
   - **Root Directory:** `/apps/web`
3. In **Variables**, add:

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://${{recoverx-api.RAILWAY_PUBLIC_DOMAIN}}` | Connects UI to live FastAPI backend |

4. In **Settings** &rarr; **Networking** &rarr; Click **Generate Domain** (e.g. `recoverx-web-production.up.railway.app`).

---

## 4. Razorpay Webhook Configuration

Once `recoverx-api` is deployed and has a public domain:

1. Log in to the [Razorpay Dashboard](https://dashboard.razorpay.com/) in **Test Mode**.
2. Navigate to **Account & Settings** &rarr; **Webhooks** &rarr; **Add New Webhook**.
3. Fill in:
   - **Webhook URL:** `https://<YOUR-API-DOMAIN>.up.railway.app/api/v1/webhooks/razorpay`
   - **Secret:** Must match the `RAZORPAY_WEBHOOK_SECRET` variable set in Railway.
   - **Alert Email:** Your email address.
   - **Active Events:**
     - `payment_link.paid`
     - `payment.failed`
     - `payment.captured`
     - `order.paid`
4. Click **Create Webhook**.

---

## 5. Deployment Verification Checklist

- [ ] `GET https://<YOUR-API-DOMAIN>/health` returns `{"status": "ok"}`.
- [ ] `GET https://<YOUR-API-DOMAIN>/ready` returns `{"status": "ok", "database": {"status": "ok"}, "redis": {"status": "ok"}}`.
- [ ] Open `https://<YOUR-WEB-DOMAIN>` in your browser &rarr; Command Center loads live metrics.
- [ ] Navigate to `/opportunities/opp_demo_01` &rarr; Click **Generate Recovery Link** &rarr; Real Razorpay short link generated.
- [ ] Complete a test payment &rarr; Razorpay fires webhook &rarr; Opportunity transitions to **`RECOVERED`**.

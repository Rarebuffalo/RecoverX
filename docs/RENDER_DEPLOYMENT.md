# RecoverX — Render Free Tier Deployment Guide ($0/mo)

This guide provides exact, zero-cost deployment instructions for **RecoverX** on the [Render](https://render.com) free tier.

---

## Architecture Overview (Architecture B — All on Render Free)

```
                       ┌──────────────────────────────────────────┐
                       │               Public Web                 │
                       └────────────────────┬─────────────────────┘
                                            │
                                            ▼
                       ┌──────────────────────────────────────────┐
                       │     recoverx-web (Next.js 14 Web)        │
                       │     https://recoverx-web.onrender.com    │
                       └────────────────────┬─────────────────────┘
                                            │ REST / JSON
                                            ▼
                       ┌──────────────────────────────────────────┐
                       │     recoverx-api (FastAPI Service)       │
                       │     https://recoverx-api.onrender.com    │
                       └────────────────────┬─────────────────────┘
                                            │
                                            ▼
                       ┌──────────────────────────────────────────┐
                       │     recoverx-postgres (Managed DB)       │
                       │     PostgreSQL 16 (Free Tier)            │
                       └──────────────────────────────────────────┘
```

### Services Deployed on Render
1. **`recoverx-postgres`**: Render Managed PostgreSQL Database (Free Tier, 1 GB storage).
2. **`recoverx-api`**: FastAPI ASGI Backend (Free Tier Web Service, Docker runtime).
3. **`recoverx-web`**: Next.js 14 Frontend (Free Tier Web Service, Docker runtime).

> **Note on Celery & Redis**: Redis and Celery worker services are **NOT** deployed on Render to keep the stack 100% within the free tier. All Celery and Redis codebase files are preserved for future scaling, while direct asynchronous recovery execution (`ActionExecutorService.execute_action`) runs natively inside FastAPI.

---

## Infrastructure Blueprint (`render.yaml`)

The repository includes a ready-to-use Render Blueprint (`render.yaml`):

```yaml
services:
  - type: web
    name: recoverx-api
    runtime: docker
    dockerContext: ./apps/api
    dockerfilePath: ./apps/api/Dockerfile
    plan: free
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: recoverx-postgres
          property: connectionString
      - key: ENVIRONMENT
        value: production
      - key: EXECUTION_MODE
        value: local_deterministic
      - key: LLM_PROVIDER
        value: mock
      - key: CORS_ORIGINS
        value: https://recoverx-web.onrender.com,http://localhost:3000
      - key: JWT_SECRET
        generateValue: true
      - key: RAZORPAY_KEY_ID
        value: ""
      - key: RAZORPAY_KEY_SECRET
        value: ""
      - key: RAZORPAY_WEBHOOK_SECRET
        value: ""

  - type: web
    name: recoverx-web
    runtime: docker
    dockerContext: ./apps/web
    dockerfilePath: ./apps/web/Dockerfile
    plan: free
    healthCheckPath: /health
    envVars:
      - key: NEXT_PUBLIC_API_BASE_URL
        value: https://recoverx-api.onrender.com

databases:
  - name: recoverx-postgres
    databaseName: recoverx_db
    user: recoverx
    plan: free
```

---

## Deployment Steps

### Method 1: Render Blueprints (Recommended — 1-Click Setup)

1. **Push Code to GitHub**:
   Ensure your RecoverX repository is pushed to your GitHub account.

2. **Connect to Render**:
   - Log in to [dashboard.render.com](https://dashboard.render.com).
   - Click **Blueprints** in the top navigation.
   - Click **New Blueprint Instance**.
   - Select your `RecoverX` GitHub repository.

3. **Apply Blueprint**:
   - Render automatically reads `render.yaml` and provisions:
     - `recoverx-postgres`
     - `recoverx-api`
     - `recoverx-web`
   - Click **Apply**.

4. **Verify Service URLs**:
   - If your Render service subdomains differ (e.g., `recoverx-api-xxxx.onrender.com`), update the respective environment variables:
     - In `recoverx-web`: `NEXT_PUBLIC_API_BASE_URL=https://<your-actual-api-subdomain>.onrender.com`
     - In `recoverx-api`: `CORS_ORIGINS=https://<your-actual-web-subdomain>.onrender.com,http://localhost:3000`

---

### Method 2: Manual Dashboard Creation

If you prefer manual setup through the Render UI:

#### 1. Create PostgreSQL Database
- Click **New +** → **PostgreSQL**.
- **Name**: `recoverx-postgres`
- **Database**: `recoverx_db`
- **User**: `recoverx`
- **Plan**: `Free`
- Click **Create Database**.
- Copy the **Internal Database URL**.

#### 2. Create FastAPI Web Service
- Click **New +** → **Web Service**.
- Connect your GitHub repository.
- **Name**: `recoverx-api`
- **Language**: `Docker`
- **Root Directory**: `apps/api`
- **Dockerfile Path**: `Dockerfile` (relative to root directory)
- **Plan**: `Free`
- **Health Check Path**: `/health`
- **Environment Variables**:
  | Variable | Value | Description |
  |---|---|---|
  | `DATABASE_URL` | `<Internal Database URL from Step 1>` | Database connection string |
  | `ENVIRONMENT` | `production` | Production environment mode |
  | `EXECUTION_MODE` | `local_deterministic` | Safe mock adapter (or `razorpay_sandbox`) |
  | `LLM_PROVIDER` | `mock` | `mock`, `gemini`, or `openai` |
  | `LLM_MODEL` | `gemini-2.5-flash` | Selected model (`gemini-2.5-flash`, `gpt-4o-mini`) |
  | `LLM_API_KEY` | `your_llm_api_key_here` | Server-side LLM secret (Optional, mock if empty) |
  | `CORS_ORIGINS` | `https://recoverx-web.onrender.com,http://localhost:3000` | Allowed origins |
  | `JWT_SECRET` | *(Random 32+ character string)* | Session security key |
- Click **Create Web Service**.

#### 3. Create Next.js Web Service
- Click **New +** → **Web Service**.
- Connect your GitHub repository.
- **Name**: `recoverx-web`
- **Language**: `Docker`
- **Root Directory**: `apps/web`
- **Dockerfile Path**: `Dockerfile` (relative to root directory)
- **Plan**: `Free`
- **Health Check Path**: `/health`
- **Environment Variables**:
  | Variable | Value | Description |
  |---|---|---|
  | `NEXT_PUBLIC_API_BASE_URL` | `https://recoverx-api.onrender.com` | Base URL of deployed API |
- Click **Create Web Service**.

---

## Automatic Database Migration & Idempotent Seeding

Upon container startup, `apps/api/Dockerfile` automatically executes:
```sh
alembic upgrade head && python -m app.db.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

1. **Alembic Migrations**: Runs schema migrations safely.
2. **Deterministic Seeding**: Inserts initial demo merchants, policies, failed orders, and benchmark opportunities.
3. **Idempotency Guarantee**: If seed data already exists (`DEMO_MERCHANT_ID`), seeding logs `"Demo data already seeded. Skipping."` and preserves existing state without overwriting or duplicating records.

---

## Health Check & Verification

Once deployed, verify your services:

1. **Liveness Probe**:
   ```sh
   curl https://recoverx-api.onrender.com/health
   # Expected response: {"status":"ok","environment":"production","timestamp":"..."}
   ```

2. **Readiness Probe**:
   ```sh
   curl https://recoverx-api.onrender.com/ready
   # Expected response:
   # {
   #   "status": "ok",
   #   "database": {"status": "ok", "latency_ms": 2.1},
   #   "redis": {"status": "disabled", "latency_ms": 0.0},
   #   "timestamp": "..."
   # }
   ```

3. **Frontend Dashboard**:
   - Open `https://recoverx-web.onrender.com/dashboard`
   - Check infrastructure probes at `https://recoverx-web.onrender.com/health`

---

## Switching to Razorpay Test Mode (Sandbox)

To test against live Razorpay Test Mode APIs:

1. In the Render Dashboard, navigate to **`recoverx-api`** → **Environment**.
2. Update the environment variables:
   ```env
   EXECUTION_MODE=razorpay_sandbox
   RAZORPAY_KEY_ID=rzp_test_YourKeyIdHere
   RAZORPAY_KEY_SECRET=YourKeySecretHere
   RAZORPAY_WEBHOOK_SECRET=YourWebhookSecretHere
   ```
3. In your Razorpay Dashboard (Test Mode):
   - Set the Webhook URL to: `https://recoverx-api.onrender.com/api/v1/webhooks/razorpay`
   - Active Events: `payment.failed`, `payment.captured`, `payment_link.paid`
   - Webhook Secret: Match `RAZORPAY_WEBHOOK_SECRET`
4. Click **Save Changes** in Render to trigger an automated redeployment.

---

## Security & Architectural Invariants Preserved

- **Row-Level Locking**: PostgreSQL transactions use `SELECT ... FOR UPDATE` ensuring atomic order and opportunity state transitions.
- **Server Authority**: Amount and currency verification strictly query PostgreSQL authority; client requests cannot alter transaction values.
- **HMAC Verification**: Razorpay webhooks verify SHA256 signatures before processing payloads.
- **Webhook Deduplication**: Processed webhook event IDs are tracked in PostgreSQL tables to prevent replay attacks.
- **Audit Logging**: Every action, policy evaluation, and outcome is logged in immutable audit records.

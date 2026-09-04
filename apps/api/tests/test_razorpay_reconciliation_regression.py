import uuid
import hashlib
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Merchant,
    Customer,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    RecoveryAction,
    MerchantPolicy,
    AuditEvent,
    ProcessedWebhook,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    ActionExecutionStatus,
    ActorType,
)
from app.services.executor.adapters.razorpay_adapter import RazorpaySandboxAdapter
from app.services.executor.adapters.base_adapter import CreatePaymentLinkRequest
from app.services.executor.adapters.razorpay_adapter import GatewayExecutionException, ProviderErrorCategory
from app.services.opportunity_service import OpportunityService


@pytest.mark.asyncio
async def test_reconcile_existing_paid_razorpay_link_via_audit_and_webhook(
    client: AsyncClient, db_session: AsyncSession
):
    """Test A: Existing paid Razorpay Payment Link -> reconcile -> RECOVERED."""
    merchant = Merchant(name="Reconcile Test Store", email="reconcile@test.com", razorpay_account_id="acc_recon_01")
    db_session.add(merchant)
    await db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        email="rahul_recon@test.com",
        name="Rahul Sharma",
        lifetime_value_inr=Decimal("25000.00"),
        total_orders=5,
        successful_orders=5,
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        provider_order_id="order_recon_8499",
        amount_inr=Decimal("8499.00"),
        status=OrderStatus.ATTEMPTED,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.DETECTED,
        revenue_at_risk_inr=Decimal("8499.00"),
        attempt_count=1,
    )
    db_session.add(opp)
    await db_session.flush()

    # Pre-existing action
    action_ref = f"recovery:{opp.id}:attempt:1"
    hashed_ref = f"rec_{hashlib.sha256(action_ref.encode('utf-8')).hexdigest()[:16]}"
    action = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=opp.id,
        action_type="CREATE_RECOVERY_PAYMENT_LINK",
        execution_status=ActionExecutionStatus.SUCCEEDED,
        provider_action_id="plink_real_paid_12345",
        payment_link_url="https://rzp.io/i/real_paid_12345",
        idempotency_key=action_ref,
    )
    db_session.add(action)

    # Processed webhook event recorded earlier
    pw = ProcessedWebhook(
        event_id="evt_recon_001",
        event_type="payment_link.paid",
        payload={
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_real_paid_12345",
                        "reference_id": hashed_ref,
                        "amount_paid": 849900,
                        "status": "paid",
                        "notes": {"opportunity_id": str(opp.id)},
                    }
                }
            }
        },
    )
    db_session.add(pw)
    await db_session.commit()

    # Call POST /api/v1/opportunities/{id}/reconcile
    res = await client.post(f"/api/v1/opportunities/{opp.id}/reconcile")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "reconciled"
    assert data["opportunity_status"] == "RECOVERED"
    assert data["recovered_amount_inr"] == 8499.0

    # Verify DB state
    await db_session.refresh(opp)
    await db_session.refresh(order)
    assert opp.status == OpportunityStatus.RECOVERED
    assert opp.recovered_amount_inr == Decimal("8499.00")
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_repeated_reconciliation_no_duplicate_recovery(
    client: AsyncClient, db_session: AsyncSession
):
    """Test B: Repeated reconciliation -> no duplicate recovery."""
    merchant = Merchant(name="Repeat Reconcile Store", email="repeat_recon@test.com")
    db_session.add(merchant)
    await db_session.flush()

    customer = Customer(merchant_id=merchant.id, email="repeat_cust@test.com")
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_inr=Decimal("5000.00"),
        status=OrderStatus.PAID,
    )
    db_session.add(order)
    await db_session.flush()

    opp = RecoveryOpportunity(
        merchant_id=merchant.id,
        order_id=order.id,
        status=OpportunityStatus.RECOVERED,
        recovered_amount_inr=Decimal("5000.00"),
        revenue_at_risk_inr=Decimal("5000.00"),
    )
    db_session.add(opp)
    await db_session.commit()

    # Repeated call
    res = await client.post(f"/api/v1/opportunities/{opp.id}/reconcile")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "already_recovered"
    assert data["opportunity_status"] == "RECOVERED"
    assert data["recovered_amount_inr"] == 5000.0


@pytest.mark.asyncio
async def test_duplicate_reference_id_reconciliation_and_adapter_fallback(
    monkeypatch, db_session: AsyncSession
):
    """Test C & D: Duplicate reference_id handled by fetching existing link rather than crashing."""
    adapter = RazorpaySandboxAdapter(key_id="rzp_test_mock", key_secret="mock_secret")

    # Mock fetch_payment_link_by_reference_id
    async def mock_fetch_by_ref(ref_id: str):
        return {
            "id": "plink_existing_12345",
            "short_url": "https://rzp.io/i/existing_12345",
            "reference_id": ref_id,
            "status": "paid",
            "amount_paid": 849900,
        }

    monkeypatch.setattr(adapter, "fetch_payment_link_by_reference_id", mock_fetch_by_ref)

    # When create_recovery_payment_link is called, simulate 400 error from Razorpay
    import httpx

    class MockResponse:
        status_code = 400
        text = '{"error": {"description": "payment link with given reference_id already exists"}}'
        def json(self):
            return {"error": {"description": "payment link with given reference_id already exists"}}

    class MockAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockAsyncClient())

    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id="recovery:44444444-4444-4444-4444-444444444441:attempt:1",
        description="Recovery Payment",
    )

    result = await adapter.create_recovery_payment_link(req)
    assert result.provider_action_id == "plink_existing_12345"
    assert result.payment_link_url == "https://rzp.io/i/existing_12345"
    assert result.status == "paid"


@pytest.mark.asyncio
async def test_consecutive_reset_demo_runs_produce_unique_reference_ids(
    client: AsyncClient, db_session: AsyncSession
):
    """Proves two consecutive Reset Demo runs produce unique Razorpay reference_ids to avoid collisions."""
    import time
    from app.db.seed import run_seeding, OPP_A_ID
    from app.services.executor.action_executor_service import ActionExecutorService

    # 1. First Reset Demo run
    await run_seeding(db_session, force=True)
    action1 = await ActionExecutorService.create_and_queue_action(
        db_session, opportunity_id=OPP_A_ID
    )
    ref_id_1 = action1.idempotency_key
    ref_hash_1 = hashlib.sha256(ref_id_1.encode("utf-8")).hexdigest()[:16]

    # Sleep slightly or advance time to guarantee distinct timestamp
    time.sleep(1.05)

    # 2. Second Reset Demo run
    await run_seeding(db_session, force=True)
    action2 = await ActionExecutorService.create_and_queue_action(
        db_session, opportunity_id=OPP_A_ID
    )
    ref_id_2 = action2.idempotency_key
    ref_hash_2 = hashlib.sha256(ref_id_2.encode("utf-8")).hexdigest()[:16]

    # 3. Assert uniqueness
    assert ref_id_1 != ref_id_2
    assert ref_hash_1 != ref_hash_2
    assert f"rec_{ref_hash_1}" != f"rec_{ref_hash_2}"
    assert f"rec_{ref_hash_1}" != "rec_f8330f3537329e52" or f"rec_{ref_hash_2}" != "rec_f8330f3537329e52"


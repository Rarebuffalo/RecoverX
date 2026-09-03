import uuid
import time
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import RecoveryOpportunity, Order, RecoveryAction, ActionExecutionStatus
from app.services.webhook_service import WebhookService
from app.services.outcome.outcome_service import RecoveryOutcomeService

router = APIRouter(prefix="/developer", tags=["Developer Simulation"])


class SimulatePaymentRequest(BaseModel):
    opportunity_id: str
    amount_inr: float | None = None
    method: str = "upi"


class SimulationResponse(BaseModel):
    status: str
    message: str
    opportunity_id: str
    order_id: str
    provider_payment_id: str
    recovered_amount_inr: float
    opportunity_status: str


@router.post("/simulate-payment-success", response_model=SimulationResponse)
async def simulate_payment_success(
    req: SimulatePaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Developer-only simulation of customer paying the recovery payment link."""
    opp = None
    try:
        opp_uuid = uuid.UUID(req.opportunity_id)
        res = await db.execute(select(RecoveryOpportunity).where(RecoveryOpportunity.id == opp_uuid))
        opp = res.scalar_one_or_none()
    except (ValueError, TypeError):
        # Fallback to first available opportunity for demo string IDs
        res = await db.execute(select(RecoveryOpportunity).limit(1))
        opp = res.scalar_one_or_none()

    if not opp:
        # If database is clean, return successful simulated payload response directly
        sim_id = str(uuid.uuid4())[:8]
        return SimulationResponse(
            status="success",
            message=f"Simulated payment capture verified for {req.opportunity_id}",
            opportunity_id=req.opportunity_id,
            order_id=f"order_{sim_id}",
            provider_payment_id=f"pay_sim_{sim_id}",
            recovered_amount_inr=req.amount_inr or 8499.0,
            opportunity_status="RECOVERED",
        )

    order_res = await db.execute(select(Order).where(Order.id == opp.order_id))
    order = order_res.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{opp.order_id}' not found.",
        )

    # Resolve amount
    amount_inr = Decimal(str(req.amount_inr)) if req.amount_inr else opp.revenue_at_risk_inr
    amount_paise = int(amount_inr * 100)

    # Generate synthetic provider IDs
    sim_id = str(uuid.uuid4())[:8]
    provider_payment_id = f"pay_sim_{sim_id}"
    event_id = f"evt_sim_{sim_id}"

    # Construct genuine payment.captured webhook payload
    synthetic_payload = {
        "entity": "event",
        "account_id": "acc_mock_merchant_01",
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": provider_payment_id,
                    "entity": "payment",
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "captured",
                    "order_id": order.provider_order_id,
                    "invoice_id": None,
                    "international": False,
                    "method": req.method,
                    "amount_refunded": 0,
                    "refund_status": None,
                    "captured": True,
                    "description": f"Simulated Recovery Payment for {order.provider_order_id}",
                    "card_id": None,
                    "bank": None,
                    "wallet": None,
                    "vpa": "customer@upi" if req.method == "upi" else None,
                    "email": "customer@example.com",
                    "contact": "+919876543210",
                    "notes": {"simulated": True},
                    "fee": 0,
                    "tax": 0,
                    "error_code": None,
                    "error_description": None,
                    "created_at": int(time.time()),
                }
            }
        },
        "created_at": int(time.time()),
    }

    # Pass payload into the standard webhook ingestion pipeline
    webhook_res = await WebhookService.process_webhook(
        db, payload=synthetic_payload, event_id_header=event_id
    )

    # Refresh opportunity
    await db.refresh(opp)

    return SimulationResponse(
        status="success",
        message="Simulated payment captured and processed through webhook pipeline.",
        opportunity_id=str(opp.id),
        order_id=str(order.id),
        provider_payment_id=provider_payment_id,
        recovered_amount_inr=float(opp.recovered_amount_inr),
        opportunity_status=opp.status.value,
    )


@router.post("/simulate-ambiguous-timeout")
async def simulate_ambiguous_timeout(
    req: SimulatePaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Simulates a network timeout during gateway execution, triggering the safe AMBIGUOUS state."""
    opp = None
    try:
        opp_uuid = uuid.UUID(req.opportunity_id)
        opp = (await db.execute(select(RecoveryOpportunity).where(RecoveryOpportunity.id == opp_uuid))).scalar_one_or_none()
    except (ValueError, TypeError):
        opp = (await db.execute(select(RecoveryOpportunity).limit(1))).scalar_one_or_none()

    if not opp:
        return {
            "status": "ambiguous",
            "action_id": f"act_sim_{str(uuid.uuid4())[:8]}",
            "execution_status": "AMBIGUOUS",
            "message": "Action transitioned to AMBIGUOUS. Blind retries blocked until manual reconciliation.",
        }

    action = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=opp.id,
        action_type="CREATE_RECOVERY_PAYMENT_LINK",
        idempotency_key=f"recovery:{opp.id}:attempt:{opp.attempt_count + 1}",
        policy_approved=True,
        execution_status=ActionExecutionStatus.AMBIGUOUS,
        error_category="GATEWAY_NETWORK_TIMEOUT",
        error_message="Gateway switch connection timed out before ACK received. Verification required.",
    )
    db.add(action)
    await db.commit()
    return {
        "status": "ambiguous",
        "action_id": str(action.id),
        "execution_status": "AMBIGUOUS",
        "message": "Action transitioned to AMBIGUOUS. Blind retries blocked until manual reconciliation.",
    }


@router.post("/simulate-failed-payment")
async def simulate_failed_payment(
    req: SimulatePaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Simulates an explicit failed payment response from the gateway."""
    opp = None
    try:
        opp_uuid = uuid.UUID(req.opportunity_id)
        opp = (await db.execute(select(RecoveryOpportunity).where(RecoveryOpportunity.id == opp_uuid))).scalar_one_or_none()
    except (ValueError, TypeError):
        opp = (await db.execute(select(RecoveryOpportunity).limit(1))).scalar_one_or_none()

    if not opp:
        return {
            "status": "failed",
            "action_id": f"act_sim_{str(uuid.uuid4())[:8]}",
            "execution_status": "FAILED",
            "message": "Action execution failed. Logged with provider error category.",
        }

    action = RecoveryAction(
        id=uuid.uuid4(),
        opportunity_id=opp.id,
        action_type="CREATE_RECOVERY_PAYMENT_LINK",
        idempotency_key=f"recovery:{opp.id}:attempt:{opp.attempt_count + 1}",
        policy_approved=True,
        execution_status=ActionExecutionStatus.FAILED,
        error_category="INVALID_CARD_DECLINE",
        error_message="Issuing bank declined payment link authorization.",
    )
    db.add(action)
    await db.commit()
    return {
        "status": "failed",
        "action_id": str(action.id),
        "execution_status": "FAILED",
        "message": "Action execution failed. Logged with provider error category.",
    }


@router.post("/reset-demo-state")
async def reset_demo_state(db: AsyncSession = Depends(get_db)):
    """Resets the developer demo state to known baseline opportunities and seeds."""
    from app.db.seed import seed_database
    await seed_database(db)
    return {
        "status": "success",
        "message": "Demo environment reset to baseline state successfully.",
    }



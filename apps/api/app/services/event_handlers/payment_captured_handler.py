import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models import (
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    RecoveryAction,
    AuditEvent,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    ActionExecutionStatus,
    ActorType,
)
from app.services.event_handlers.base_handler import BaseEventHandler
from app.services.event_handlers.common import resolve_merchant, get_or_create_customer, resolve_recovery_target


class PaymentCapturedHandler(BaseEventHandler):
    """Processes 'payment.captured' webhook events."""

    async def handle(
        self,
        db: AsyncSession,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        account_id: str | None = None,
    ) -> Dict[str, Any]:
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not payment_entity:
            raise ValueError("Missing 'payment.entity' in webhook payload.")

        provider_payment_id = payment_entity.get("id")
        provider_order_id = payment_entity.get("order_id")
        notes = payment_entity.get("notes") or {}
        raw_amount = payment_entity.get("amount", 0)
        amount_inr = Decimal(str(raw_amount)) / Decimal("100.00")
        method = payment_entity.get("method", "unknown")
        email = payment_entity.get("email")
        phone = payment_entity.get("contact")

        # 1. Resolve Merchant
        merchant = await resolve_merchant(db, account_id=account_id)
        if not merchant:
            raise ValueError(f"Merchant could not be resolved for account_id '{account_id}'.")

        # 2. Multi-Vector Entity Resolution
        order, opportunity, action = await resolve_recovery_target(
            db,
            merchant_id=merchant.id,
            notes=notes,
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
        )

        # 3. Resolve or Create Customer & Update Stats
        customer = await get_or_create_customer(db, merchant.id, email=email, phone=phone)
        customer.successful_orders += 1
        customer.total_orders += 1
        customer.lifetime_value_inr += amount_inr
        customer.updated_at = datetime.now(timezone.utc)

        # 4. Locate or Create Order with Row-Level Lock
        if not order:
            order = Order(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                customer_id=customer.id,
                provider_order_id=provider_order_id,
                amount_inr=amount_inr,
                currency="INR",
                status=OrderStatus.PAID,
            )
            db.add(order)
            await db.flush()
        else:
            order.status = OrderStatus.PAID
            order.updated_at = datetime.now(timezone.utc)

        # 5. Upsert Payment Attempt
        attempt_query = select(PaymentAttempt).where(
            PaymentAttempt.provider_payment_id == provider_payment_id
        ).with_for_update()
        attempt_res = await db.execute(attempt_query)
        attempt = attempt_res.scalar_one_or_none()

        if not attempt:
            attempt = PaymentAttempt(
                id=uuid.uuid4(),
                order_id=order.id,
                merchant_id=merchant.id,
                provider_payment_id=provider_payment_id,
                method=method,
                status=PaymentAttemptStatus.CAPTURED,
                amount_inr=amount_inr,
            )
            db.add(attempt)
        else:
            attempt.status = PaymentAttemptStatus.CAPTURED
            attempt.updated_at = datetime.now(timezone.utc)

        await db.flush()

        # 6. Reconcile / Preempt Recovery Opportunity
        recovered_opportunity = False
        if not opportunity and order:
            opp_query = (
                select(RecoveryOpportunity)
                .where(RecoveryOpportunity.order_id == order.id)
                .with_for_update()
            )
            opp_res = await db.execute(opp_query)
            opportunity = opp_res.scalar_one_or_none()

        if opportunity and opportunity.status not in [OpportunityStatus.RECOVERED, OpportunityStatus.CLOSED_UNRECOVERED]:
            opportunity.status = OpportunityStatus.RECOVERED
            opportunity.recovered_amount_inr = amount_inr
            opportunity.resolved_at = datetime.now(timezone.utc)
            opportunity.updated_at = datetime.now(timezone.utc)
            recovered_opportunity = True

            # Audit event for Opportunity Recovery
            audit_opp = AuditEvent(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                opportunity_id=opportunity.id,
                actor_type=ActorType.SYSTEM,
                event_type="REVENUE_RECOVERED",
                event_summary=f"Opportunity transitioned to RECOVERED: payment {provider_payment_id} captured (₹{amount_inr})",
                event_data={
                    "order_id": str(order.id),
                    "provider_payment_id": provider_payment_id,
                    "recovered_amount_inr": str(amount_inr),
                },
            )
            db.add(audit_opp)

            if action:
                action.execution_status = ActionExecutionStatus.SUCCEEDED
                action.completed_at = datetime.now(timezone.utc)
            elif opportunity.actions:
                for act in opportunity.actions:
                    act.execution_status = ActionExecutionStatus.SUCCEEDED
                    act.completed_at = datetime.now(timezone.utc)

        # 7. Audit Event for Payment Captured
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            opportunity_id=opportunity.id if opportunity else None,
            actor_type=ActorType.SYSTEM,
            event_type="PAYMENT_CAPTURED_PROCESSED",
            event_summary=f"Processed payment.captured for {provider_payment_id} (₹{amount_inr})",
            event_data={
                "event_id": event_id,
                "provider_payment_id": provider_payment_id,
                "provider_order_id": provider_order_id,
                "amount_inr": str(amount_inr),
                "recovered_opportunity": recovered_opportunity,
            },
        )
        db.add(audit_event)

        logger.info(
            "Processed payment.captured event",
            event_id=event_id,
            payment_id=provider_payment_id,
            order_id=str(order.id),
            opportunity_id=str(opportunity.id) if opportunity else None,
            recovered_opportunity=recovered_opportunity,
        )

        return {
            "order_id": str(order.id),
            "payment_id": provider_payment_id,
            "opportunity_id": str(opportunity.id) if opportunity else None,
            "recovered_opportunity": recovered_opportunity,
        }

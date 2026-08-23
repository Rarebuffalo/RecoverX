import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models import (
    Merchant,
    Order,
    PaymentAttempt,
    RecoveryOpportunity,
    AuditEvent,
    OrderStatus,
    PaymentAttemptStatus,
    OpportunityStatus,
    ActorType,
)
from app.services.event_handlers.base_handler import BaseEventHandler
from app.services.event_handlers.common import resolve_merchant, get_or_create_customer


class PaymentFailedHandler(BaseEventHandler):
    """Processes 'payment.failed' webhook events."""

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
        raw_amount = payment_entity.get("amount", 0)
        amount_inr = Decimal(str(raw_amount)) / Decimal("100.00")
        method = payment_entity.get("method", "unknown")
        error_code = payment_entity.get("error_code")
        error_description = payment_entity.get("error_description")
        email = payment_entity.get("email")
        phone = payment_entity.get("contact")

        # 1. Resolve Merchant
        merchant = await resolve_merchant(db, account_id=account_id)
        if not merchant:
            raise ValueError(f"Merchant could not be resolved for account_id '{account_id}'.")

        # 2. Resolve or Create Customer
        customer = await get_or_create_customer(db, merchant.id, email=email, phone=phone)

        # 3. Locate or Create Order with Row-Level Lock
        order = None
        if provider_order_id:
            query = (
                select(Order)
                .where(Order.merchant_id == merchant.id, Order.provider_order_id == provider_order_id)
                .with_for_update()
            )
            result = await db.execute(query)
            order = result.scalar_one_or_none()

        if not order:
            order = Order(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                customer_id=customer.id,
                provider_order_id=provider_order_id,
                amount_inr=amount_inr,
                currency="INR",
                status=OrderStatus.ATTEMPTED,
            )
            db.add(order)
            await db.flush()
        else:
            # Order state precedence: Never downgrade a 'paid' order to 'attempted'
            if order.status != OrderStatus.PAID:
                order.status = OrderStatus.ATTEMPTED
                order.updated_at = datetime.now(timezone.utc)

        # 4. Upsert Payment Attempt
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
                status=PaymentAttemptStatus.FAILED,
                amount_inr=amount_inr,
                failure_code=error_code,
                failure_reason=error_description,
            )
            db.add(attempt)
        else:
            attempt.status = PaymentAttemptStatus.FAILED
            attempt.failure_code = error_code
            attempt.failure_reason = error_description
            attempt.updated_at = datetime.now(timezone.utc)

        await db.flush()

        # 5. Create Recovery Opportunity if Order is not already paid
        created_opportunity = False
        if order.status != OrderStatus.PAID:
            opp_query = (
                select(RecoveryOpportunity)
                .where(RecoveryOpportunity.order_id == order.id)
                .with_for_update()
            )
            opp_res = await db.execute(opp_query)
            opportunity = opp_res.scalar_one_or_none()

            if not opportunity:
                opportunity = RecoveryOpportunity(
                    id=uuid.uuid4(),
                    merchant_id=merchant.id,
                    order_id=order.id,
                    status=OpportunityStatus.DETECTED,
                    revenue_at_risk_inr=order.amount_inr,
                    recovered_amount_inr=Decimal("0.00"),
                    attempt_count=0,
                )
                db.add(opportunity)
                await db.flush()
                created_opportunity = True

                # Audit Event for Opportunity Detection
                audit_opp = AuditEvent(
                    id=uuid.uuid4(),
                    merchant_id=merchant.id,
                    opportunity_id=opportunity.id,
                    actor_type=ActorType.SYSTEM,
                    event_type="RECOVERY_OPPORTUNITY_CREATED",
                    event_summary=f"Recovery opportunity detected for failed payment {provider_payment_id} (₹{order.amount_inr})",
                    event_data={
                        "order_id": str(order.id),
                        "provider_payment_id": provider_payment_id,
                        "failure_code": error_code,
                        "revenue_at_risk_inr": str(order.amount_inr),
                    },
                )
                db.add(audit_opp)

        # 6. Audit Event for Payment Failed
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            opportunity_id=None,
            actor_type=ActorType.SYSTEM,
            event_type="PAYMENT_FAILED_PROCESSED",
            event_summary=f"Processed payment.failed for {provider_payment_id} (Code: {error_code})",
            event_data={
                "event_id": event_id,
                "provider_payment_id": provider_payment_id,
                "provider_order_id": provider_order_id,
                "amount_inr": str(amount_inr),
                "failure_code": error_code,
                "created_opportunity": created_opportunity,
            },
        )
        db.add(audit_event)

        logger.info(
            "Processed payment.failed event",
            event_id=event_id,
            payment_id=provider_payment_id,
            order_id=str(order.id),
            created_opportunity=created_opportunity,
        )

        return {
            "order_id": str(order.id),
            "payment_id": provider_payment_id,
            "created_opportunity": created_opportunity,
        }

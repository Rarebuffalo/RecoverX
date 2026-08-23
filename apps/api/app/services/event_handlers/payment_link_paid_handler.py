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
from app.services.event_handlers.common import resolve_merchant, get_or_create_customer


class PaymentLinkPaidHandler(BaseEventHandler):
    """Processes 'payment_link.paid' webhook events."""

    async def handle(
        self,
        db: AsyncSession,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        account_id: str | None = None,
    ) -> Dict[str, Any]:
        plink_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

        provider_plink_id = plink_entity.get("id")
        provider_order_id = plink_entity.get("order_id") or payment_entity.get("order_id")
        raw_amount = plink_entity.get("amount_paid") or plink_entity.get("amount", 0)
        amount_inr = Decimal(str(raw_amount)) / Decimal("100.00")
        provider_payment_id = payment_entity.get("id")

        # 1. Resolve Merchant
        merchant = await resolve_merchant(db, account_id=account_id)
        if not merchant:
            raise ValueError(f"Merchant could not be resolved for account_id '{account_id}'.")

        # 2. Locate Order with Row-Level Lock
        order = None
        if provider_order_id:
            query = (
                select(Order)
                .where(Order.merchant_id == merchant.id, Order.provider_order_id == provider_order_id)
                .with_for_update()
            )
            result = await db.execute(query)
            order = result.scalar_one_or_none()

        if order:
            order.status = OrderStatus.PAID
            order.updated_at = datetime.now(timezone.utc)

            # 3. Upsert Payment Attempt if payment entity exists
            if provider_payment_id:
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
                        method=payment_entity.get("method", "payment_link"),
                        status=PaymentAttemptStatus.CAPTURED,
                        amount_inr=amount_inr,
                    )
                    db.add(attempt)
                else:
                    attempt.status = PaymentAttemptStatus.CAPTURED
                    attempt.updated_at = datetime.now(timezone.utc)

            # 4. Reconcile Recovery Opportunity & Recovery Action
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

                # Find any associated action
                action_query = (
                    select(RecoveryAction)
                    .where(RecoveryAction.opportunity_id == opportunity.id)
                    .with_for_update()
                )
                action_res = await db.execute(action_query)
                for action in action_res.scalars().all():
                    if action.provider_action_id == provider_plink_id or not action.provider_action_id:
                        action.execution_status = ActionExecutionStatus.SUCCESS
                        action.provider_action_id = provider_plink_id
                        action.executed_at = datetime.now(timezone.utc)

        # 5. Audit Event for Payment Link Paid
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            opportunity_id=opportunity.id if order and opportunity else None,
            actor_type=ActorType.SYSTEM,
            event_type="PAYMENT_LINK_PAID_PROCESSED",
            event_summary=f"Processed payment_link.paid for {provider_plink_id} (₹{amount_inr})",
            event_data={
                "event_id": event_id,
                "provider_plink_id": provider_plink_id,
                "provider_order_id": provider_order_id,
                "provider_payment_id": provider_payment_id,
                "amount_inr": str(amount_inr),
            },
        )
        db.add(audit_event)

        logger.info(
            "Processed payment_link.paid event",
            event_id=event_id,
            plink_id=provider_plink_id,
            order_id=str(order.id) if order else None,
        )

        return {
            "order_id": str(order.id) if order else None,
            "plink_id": provider_plink_id,
        }

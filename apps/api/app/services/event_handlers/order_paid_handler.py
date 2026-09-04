import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models import (
    Order,
    RecoveryOpportunity,
    RecoveryAction,
    AuditEvent,
    OrderStatus,
    OpportunityStatus,
    ActionExecutionStatus,
    ActorType,
)
from app.services.event_handlers.base_handler import BaseEventHandler
from app.services.event_handlers.common import resolve_merchant, resolve_recovery_target


class OrderPaidHandler(BaseEventHandler):
    """Processes 'order.paid' webhook events for state consistency and reconciliation."""

    async def handle(
        self,
        db: AsyncSession,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        account_id: str | None = None,
    ) -> Dict[str, Any]:
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        if not order_entity:
            raise ValueError("Missing 'order.entity' in webhook payload.")

        provider_order_id = order_entity.get("id")
        notes = order_entity.get("notes") or {}
        raw_amount = order_entity.get("amount_paid") or order_entity.get("amount", 0)
        amount_inr = Decimal(str(raw_amount)) / Decimal("100.00")

        # 1. Resolve Merchant
        merchant = await resolve_merchant(db, account_id=account_id)
        if not merchant:
            raise ValueError(f"Merchant could not be resolved for account_id '{account_id}'.")

        # 2. Multi-Vector Entity Resolution with Row-Level Lock
        order, opportunity, action = await resolve_recovery_target(
            db,
            merchant_id=merchant.id,
            notes=notes,
            provider_order_id=provider_order_id,
        )

        if not order:
            logger.warning(
                "Order for order.paid event not found in RecoverX database. Awaiting payment event.",
                provider_order_id=provider_order_id,
            )
            return {"status": "order_not_found", "provider_order_id": provider_order_id}

        order.status = OrderStatus.PAID
        order.updated_at = datetime.now(timezone.utc)

        # 3. Reconcile Recovery Opportunity
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

            # Audit event for REVENUE_RECOVERED
            audit_opp = AuditEvent(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                opportunity_id=opportunity.id,
                actor_type=ActorType.SYSTEM,
                event_type="REVENUE_RECOVERED",
                event_summary=f"Revenue recovery confirmed: order {provider_order_id} marked paid (₹{amount_inr})",
                event_data={
                    "order_id": str(order.id),
                    "opportunity_id": str(opportunity.id),
                    "provider_order_id": provider_order_id,
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

        # 4. Audit Event for Order Paid
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            opportunity_id=opportunity.id if opportunity else None,
            actor_type=ActorType.SYSTEM,
            event_type="ORDER_PAID_PROCESSED",
            event_summary=f"Processed order.paid reconciliation for {provider_order_id} (₹{amount_inr})",
            event_data={
                "event_id": event_id,
                "provider_order_id": provider_order_id,
                "amount_inr": str(amount_inr),
                "recovered_opportunity": recovered_opportunity,
            },
        )
        db.add(audit_event)

        logger.info(
            "Processed order.paid event",
            event_id=event_id,
            order_id=str(order.id),
            provider_order_id=provider_order_id,
            opportunity_id=str(opportunity.id) if opportunity else None,
            recovered_opportunity=recovered_opportunity,
        )

        return {
            "order_id": str(order.id),
            "provider_order_id": provider_order_id,
            "opportunity_id": str(opportunity.id) if opportunity else None,
            "recovered_opportunity": recovered_opportunity,
        }

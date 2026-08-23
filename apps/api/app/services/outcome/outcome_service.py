import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import (
    RecoveryOpportunity,
    RecoveryAction,
    Order,
    AuditEvent,
    ActorType,
    OpportunityStatus,
    ActionExecutionStatus,
)
from app.core.logging import logger


class RecoveryOutcomeService:
    """Outcome and settlement engine verifying payment evidence and updating recovered revenue."""

    @classmethod
    async def record_payment_recovery(
        cls,
        db: AsyncSession,
        order_id: uuid.UUID,
        provider_payment_id: str,
        amount_inr: Decimal,
        payment_timestamp: Optional[datetime] = None,
    ) -> Optional[RecoveryOpportunity]:
        query = (
            select(RecoveryOpportunity)
            .where(RecoveryOpportunity.order_id == order_id)
            .options(
                selectinload(RecoveryOpportunity.order),
                selectinload(RecoveryOpportunity.actions),
            )
        )
        res = await db.execute(query)
        opp = res.scalar_one_or_none()
        if not opp:
            logger.info("No recovery opportunity associated with paid order", order_id=str(order_id))
            return None

        now = payment_timestamp or datetime.now(timezone.utc)

        # ----------------------------------------------------
        # 1. Double-Counting Prevention
        # ----------------------------------------------------
        if opp.status == OpportunityStatus.RECOVERED and opp.recovered_amount_inr >= opp.revenue_at_risk_inr:
            logger.info(
                "Duplicate payment capture event received for already recovered opportunity",
                opportunity_id=str(opp.id),
                provider_payment_id=provider_payment_id,
            )
            return opp

        # ----------------------------------------------------
        # 2. Causality & Amount Reconciliation
        # ----------------------------------------------------
        expected_amount = opp.revenue_at_risk_inr or opp.order.amount_inr
        is_full_recovery = amount_inr >= expected_amount

        opp.recovered_amount_inr = amount_inr
        opp.resolved_at = now
        opp.updated_at = now

        if is_full_recovery:
            opp.status = OpportunityStatus.RECOVERED
        else:
            opp.status = OpportunityStatus.PARTIALLY_RECOVERED

        # Update latest recovery action if present
        if opp.actions:
            latest_action = opp.actions[-1]
            if latest_action.execution_status in [
                ActionExecutionStatus.PENDING,
                ActionExecutionStatus.QUEUED,
                ActionExecutionStatus.EXECUTING,
                ActionExecutionStatus.SUCCEEDED,
            ]:
                latest_action.execution_status = ActionExecutionStatus.SUCCEEDED
                latest_action.completed_at = now

        # ----------------------------------------------------
        # 3. Immutable Audit Record
        # ----------------------------------------------------
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=opp.merchant_id,
            opportunity_id=opp.id,
            actor_type=ActorType.SYSTEM,
            event_type="RECOVERY_CONFIRMED" if is_full_recovery else "RECOVERY_PARTIAL",
            event_summary=(
                f"Revenue recovery confirmed: ₹{amount_inr} captured via payment '{provider_payment_id}'."
            ),
            event_data={
                "order_id": str(order_id),
                "opportunity_id": str(opp.id),
                "provider_payment_id": provider_payment_id,
                "recovered_amount_inr": float(amount_inr),
                "full_recovery": is_full_recovery,
            },
        )
        db.add(audit_event)
        await db.commit()
        await db.refresh(opp)
        return opp

    @classmethod
    async def get_recovery_metrics(
        cls, db: AsyncSession, merchant_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Calculates cohort recovery metrics across all opportunities."""
        query = select(RecoveryOpportunity)
        if merchant_id:
            query = query.where(RecoveryOpportunity.merchant_id == merchant_id)

        res = await db.execute(query)
        opps = res.scalars().all()

        total_opportunities = len(opps)
        recovered_opportunities = sum(1 for o in opps if o.status == OpportunityStatus.RECOVERED)
        active_opportunities = sum(
            1 for o in opps if o.status in [OpportunityStatus.DETECTED, OpportunityStatus.INTERVENED, OpportunityStatus.ESCALATED]
        )

        total_revenue_at_risk = sum(float(o.revenue_at_risk_inr) for o in opps)
        total_recovered_revenue = sum(float(o.recovered_amount_inr) for o in opps)

        recovery_rate = (
            round(total_recovered_revenue / total_revenue_at_risk, 4)
            if total_revenue_at_risk > 0
            else 0.0
        )

        return {
            "total_opportunities": total_opportunities,
            "recovered_opportunities": recovered_opportunities,
            "active_opportunities": active_opportunities,
            "total_revenue_at_risk_inr": total_revenue_at_risk,
            "total_recovered_revenue_inr": total_recovered_revenue,
            "recovery_rate": recovery_rate,
        }

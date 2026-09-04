import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import (
    RecoveryAction,
    RecoveryOpportunity,
    Order,
    Merchant,
    MerchantPolicy,
    AuditEvent,
    ActorType,
    OrderStatus,
    OpportunityStatus,
    ActionExecutionStatus,
    RecoveryActionType,
    ProviderErrorCategory,
)
from app.services.executor.adapters.factory import get_gateway_adapter
from app.services.executor.adapters.base_adapter import (
    BasePaymentGatewayAdapter,
    CreatePaymentLinkRequest,
    GatewayPaymentLinkResult,
)
from app.services.executor.adapters.razorpay_adapter import GatewayExecutionException
from app.services.policy_engine import PolicyEngine
from app.services.opportunity_service import resolve_opportunity_id
from app.core.config import settings
from app.core.logging import logger


class ActionExecutorService:
    """Deterministic, policy-bounded execution service for recovery actions."""

    @classmethod
    async def create_and_queue_action(
        cls,
        db: AsyncSession,
        opportunity_id: uuid.UUID | str,
        decision_id: Optional[uuid.UUID] = None,
        action_type: RecoveryActionType = RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
    ) -> RecoveryAction:
        target_id = resolve_opportunity_id(opportunity_id)
        query = (
            select(RecoveryOpportunity)
            .where(RecoveryOpportunity.id == target_id)
            .options(
                selectinload(RecoveryOpportunity.order),
                selectinload(RecoveryOpportunity.actions),
            )
        )
        res = await db.execute(query)
        opp = res.scalar_one_or_none()
        if not opp:
            raise ValueError(f"Recovery Opportunity '{opportunity_id}' not found.")

        attempt_num = opp.attempt_count + 1
        idempotency_key = f"recovery:{opp.id}:attempt:{attempt_num}"

        # Check existing action with same idempotency key
        existing_res = await db.execute(
            select(RecoveryAction).where(RecoveryAction.idempotency_key == idempotency_key)
        )
        existing_action = existing_res.scalar_one_or_none()
        if existing_action:
            return existing_action

        action = RecoveryAction(
            id=uuid.uuid4(),
            opportunity_id=opp.id,
            decision_id=decision_id,
            action_type=action_type,
            idempotency_key=idempotency_key,
            attempt_number=attempt_num,
            policy_approved=True,
            execution_status=ActionExecutionStatus.QUEUED,
            action_payload={
                "amount_inr": float(opp.order.amount_inr),
                "order_id": str(opp.order_id),
                "attempt_number": attempt_num,
            },
        )
        db.add(action)

        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=opp.merchant_id,
            opportunity_id=opp.id,
            actor_type=ActorType.EXECUTOR,
            event_type="ACTION_QUEUED",
            event_summary=f"Action '{action_type.value}' queued with idempotency key '{idempotency_key}'.",
            event_data={"action_id": str(action.id), "idempotency_key": idempotency_key},
        )
        db.add(audit_event)
        await db.commit()
        await db.refresh(action)
        return action

    @classmethod
    async def execute_action(
        cls,
        db: AsyncSession,
        action_id: uuid.UUID,
        adapter_override: Optional[BasePaymentGatewayAdapter] = None,
    ) -> Tuple[RecoveryAction, Optional[GatewayPaymentLinkResult]]:
        """Safely executes an action with pre-checks, adapter invocation, and state machine management."""
        query = (
            select(RecoveryAction)
            .where(RecoveryAction.id == action_id)
            .options(
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.order).selectinload(Order.customer),
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.merchant).selectinload(Merchant.policy),
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.actions),
            )
        )
        res = await db.execute(query)
        action = res.scalar_one_or_none()
        if not action:
            raise ValueError(f"RecoveryAction '{action_id}' not found.")

        opp = action.opportunity
        order = opp.order
        merchant = opp.merchant
        policy = merchant.policy if merchant else None

        # ----------------------------------------------------
        # 1. Idempotency Check: Already in terminal state?
        # ----------------------------------------------------
        if action.execution_status in [
            ActionExecutionStatus.SUCCEEDED,
            ActionExecutionStatus.CANCELLED,
            ActionExecutionStatus.BLOCKED,
        ]:
            logger.info("Action is already resolved, skipping execution", action_id=str(action.id), status=action.execution_status.value)
            return action, None

        # ----------------------------------------------------
        # 2. Pre-Execution Safety Check
        # ----------------------------------------------------
        # Guard A: Order is already paid
        if order.status == OrderStatus.PAID:
            action.execution_status = ActionExecutionStatus.CANCELLED
            action.error_category = "ORDER_ALREADY_PAID"
            action.error_message = "Order was confirmed paid before action execution."
            action.completed_at = datetime.now(timezone.utc)
            db.add(AuditEvent(
                id=uuid.uuid4(),
                merchant_id=opp.merchant_id,
                opportunity_id=opp.id,
                actor_type=ActorType.EXECUTOR,
                event_type="ACTION_CANCELLED",
                event_summary="Action execution cancelled: Order is already paid.",
                event_data={"action_id": str(action.id)},
            ))
            await db.commit()
            return action, None

        # Guard B: Opportunity is terminal
        if opp.status in [OpportunityStatus.RECOVERED, OpportunityStatus.CLOSED_UNRECOVERED]:
            action.execution_status = ActionExecutionStatus.CANCELLED
            action.error_category = "OPPORTUNITY_TERMINAL"
            action.error_message = f"Opportunity is in terminal state '{opp.status.value}'."
            action.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return action, None

        # ----------------------------------------------------
        # 3. Transition to EXECUTING & Commit state before API call
        # ----------------------------------------------------
        action.execution_status = ActionExecutionStatus.EXECUTING
        action.executed_at = datetime.now(timezone.utc)
        await db.commit()

        # ----------------------------------------------------
        # 4. Invoke Gateway Adapter
        # ----------------------------------------------------
        adapter = adapter_override or get_gateway_adapter()

        # Authoritative server-side amount calculation in paise
        amount_paise = int(round(float(order.amount_inr) * 100))
        customer = order.customer

        req = CreatePaymentLinkRequest(
            amount_paise=amount_paise,
            currency=order.currency or "INR",
            reference_id=action.idempotency_key,
            description=f"RecoverX: Recovery Payment for Order #{order.provider_order_id or str(order.id)[:8]}",
            customer_name=customer.name if customer else None,
            customer_email=customer.email if customer else None,
            customer_contact=customer.phone if customer else None,
            notes={
                "action_id": str(action.id),
                "opportunity_id": str(opp.id),
                "merchant_id": str(opp.merchant_id),
            },
        )

        logger.info(
            "Invoking Gateway Adapter for Recovery Action",
            action_id=str(action.id),
            execution_mode=settings.EXECUTION_MODE,
            selected_adapter=adapter.adapter_name,
            razorpay_key_id_present=bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_ID.strip()),
            razorpay_key_secret_present=bool(settings.RAZORPAY_KEY_SECRET and settings.RAZORPAY_KEY_SECRET.strip()),
            idempotency_key=action.idempotency_key,
            amount_paise=amount_paise,
        )

        try:
            gw_result = await adapter.create_recovery_payment_link(req)

            # ----------------------------------------------------
            # 5. Success State Transition
            # ----------------------------------------------------
            action.execution_status = ActionExecutionStatus.SUCCEEDED
            action.provider_action_id = gw_result.provider_action_id
            action.payment_link_url = gw_result.payment_link_url
            action.execution_response = gw_result.raw_response
            action.completed_at = datetime.now(timezone.utc)

            # Check if retrieved/created link was already paid
            is_already_paid = (
                gw_result.status == "paid"
                or (
                    isinstance(gw_result.raw_response, dict)
                    and (
                        gw_result.raw_response.get("status") == "paid"
                        or gw_result.raw_response.get("amount_paid", 0) >= amount_paise
                    )
                )
            )

            if is_already_paid:
                opp.status = OpportunityStatus.RECOVERED
                opp.recovered_amount_inr = order.amount_inr
                opp.resolved_at = datetime.now(timezone.utc)
                order.status = OrderStatus.PAID
                order.updated_at = datetime.now(timezone.utc)
                db.add(AuditEvent(
                    id=uuid.uuid4(),
                    merchant_id=opp.merchant_id,
                    opportunity_id=opp.id,
                    actor_type=ActorType.EXECUTOR,
                    event_type="REVENUE_RECOVERED",
                    event_summary=f"Revenue recovery confirmed: ₹{order.amount_inr} already paid via link {gw_result.provider_action_id}",
                    event_data={
                        "action_id": str(action.id),
                        "provider_action_id": gw_result.provider_action_id,
                        "recovered_amount_inr": str(order.amount_inr),
                        "reconciliation_source": "execution_gateway_match",
                    },
                ))
            else:
                opp.status = OpportunityStatus.INTERVENED

            opp.attempt_count += 1
            opp.last_attempt_at = datetime.now(timezone.utc)
            opp.updated_at = datetime.now(timezone.utc)

            db.add(AuditEvent(
                id=uuid.uuid4(),
                merchant_id=opp.merchant_id,
                opportunity_id=opp.id,
                actor_type=ActorType.EXECUTOR,
                event_type="PAYMENT_LINK_CREATED",
                event_summary=f"Recovery Payment Link created: {gw_result.payment_link_url}",
                event_data={
                    "action_id": str(action.id),
                    "provider_action_id": gw_result.provider_action_id,
                    "payment_link_url": gw_result.payment_link_url,
                    "amount_inr": float(order.amount_inr),
                    "adapter": adapter.adapter_name,
                    "is_already_paid": is_already_paid,
                },
            ))
            await db.commit()
            return action, gw_result

        except GatewayExecutionException as ge:
            logger.error("Gateway execution error", category=ge.category.value, message=ge.message)

            if ge.category in [ProviderErrorCategory.TIMEOUT, ProviderErrorCategory.AMBIGUOUS]:
                action.execution_status = ActionExecutionStatus.AMBIGUOUS
            else:
                action.execution_status = ActionExecutionStatus.FAILED

            action.error_category = ge.category.value
            action.error_message = ge.message[:490]
            action.completed_at = datetime.now(timezone.utc)
            action.execution_response = ge.raw_response

            db.add(AuditEvent(
                id=uuid.uuid4(),
                merchant_id=opp.merchant_id,
                opportunity_id=opp.id,
                actor_type=ActorType.EXECUTOR,
                event_type=f"ACTION_EXECUTION_{action.execution_status.value}",
                event_summary=f"Execution error ({ge.category.value}): {ge.message[:200]}",
                event_data={
                    "action_id": str(action.id),
                    "error_category": ge.category.value,
                    "error_message": ge.message,
                },
            ))
            await db.commit()
            return action, None

        except Exception as e:
            logger.error("Unexpected execution exception", error=str(e))
            action.execution_status = ActionExecutionStatus.AMBIGUOUS
            action.error_category = ProviderErrorCategory.AMBIGUOUS.value
            action.error_message = f"Unexpected exception: {str(e)[:450]}"
            action.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return action, None

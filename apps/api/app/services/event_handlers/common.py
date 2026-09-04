import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer


async def resolve_merchant(db: AsyncSession, account_id: str | None = None) -> Merchant | None:
    """Resolves merchant by Razorpay account_id, or falls back to the default active merchant."""
    if account_id:
        query = select(Merchant).where(Merchant.razorpay_account_id == account_id).limit(1)
        result = await db.execute(query)
        merchant = result.scalar_one_or_none()
        if merchant:
            return merchant

    # Fallback to the first active merchant in the system
    query = select(Merchant).where(Merchant.is_active.is_(True)).order_by(Merchant.created_at.asc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_or_create_customer(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    email: str | None,
    phone: str | None = None,
    name: str | None = None,
) -> Customer:
    """Gets an existing customer by (merchant_id, email) or creates a new customer record."""
    clean_email = email.strip().lower() if email else f"customer_{uuid.uuid4().hex[:8]}@example.com"
    
    query = select(Customer).where(
        Customer.merchant_id == merchant_id,
        Customer.email == clean_email,
    ).limit(1)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            email=clean_email,
            phone=phone,
            name=name or clean_email.split("@")[0].capitalize(),
            lifetime_value_inr=Decimal("0.00"),
            total_orders=0,
            successful_orders=0,
        )
        db.add(customer)
        await db.flush()
        
    return customer


async def resolve_recovery_target(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    provider_plink_id: str | None = None,
    reference_id: str | None = None,
    notes: dict | None = None,
    provider_order_id: str | None = None,
    provider_payment_id: str | None = None,
):
    """Multi-vector lookup resolving (Order, RecoveryOpportunity, RecoveryAction) with row-level locks.

    Resolution Strategy Priority:
    1. Provider Payment Link ID -> RecoveryAction.provider_action_id
    2. Notes Metadata -> opportunity_id or action_id
    3. Reference ID / Idempotency Key -> RecoveryAction.idempotency_key
    4. Provider Order ID -> Order.provider_order_id
    5. Provider Payment ID -> PaymentAttempt.provider_payment_id
    """
    from sqlalchemy.orm import selectinload
    from app.models import Order, RecoveryOpportunity, RecoveryAction, PaymentAttempt

    # 1. Strategy: Match by provider_plink_id
    if provider_plink_id:
        act_query = (
            select(RecoveryAction)
            .where(RecoveryAction.provider_action_id == provider_plink_id)
            .options(
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.order),
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.actions),
            )
            .with_for_update()
        )
        act_res = await db.execute(act_query)
        act = act_res.scalar_one_or_none()
        if act and act.opportunity:
            return act.opportunity.order, act.opportunity, act

    # 2. Strategy: Match by notes metadata
    if notes:
        opp_id_str = notes.get("opportunity_id")
        if opp_id_str:
            try:
                opp_uuid = uuid.UUID(str(opp_id_str))
                opp_query = (
                    select(RecoveryOpportunity)
                    .where(RecoveryOpportunity.id == opp_uuid)
                    .options(
                        selectinload(RecoveryOpportunity.order),
                        selectinload(RecoveryOpportunity.actions),
                    )
                    .with_for_update()
                )
                opp_res = await db.execute(opp_query)
                opp = opp_res.scalar_one_or_none()
                if opp:
                    act = opp.actions[-1] if opp.actions else None
                    return opp.order, opp, act
            except (ValueError, TypeError):
                pass

        act_id_str = notes.get("action_id")
        if act_id_str:
            try:
                act_uuid = uuid.UUID(str(act_id_str))
                act_query = (
                    select(RecoveryAction)
                    .where(RecoveryAction.id == act_uuid)
                    .options(
                        selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.order),
                        selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.actions),
                    )
                    .with_for_update()
                )
                act_res = await db.execute(act_query)
                act = act_res.scalar_one_or_none()
                if act and act.opportunity:
                    return act.opportunity.order, act.opportunity, act
            except (ValueError, TypeError):
                pass

    # 3. Strategy: Match by reference_id / idempotency_key
    if reference_id:
        ref_query = (
            select(RecoveryAction)
            .where(RecoveryAction.idempotency_key == reference_id)
            .options(
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.order),
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.actions),
            )
            .with_for_update()
        )
        ref_res = await db.execute(ref_query)
        act = ref_res.scalar_one_or_none()
        if not act and reference_id.startswith("rec_"):
            import hashlib
            all_acts_query = select(RecoveryAction).options(
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.order),
                selectinload(RecoveryAction.opportunity).selectinload(RecoveryOpportunity.actions),
            ).with_for_update()
            all_acts_res = await db.execute(all_acts_query)
            for a in all_acts_res.scalars().all():
                if a.idempotency_key:
                    h = f"rec_{hashlib.sha256(a.idempotency_key.encode('utf-8')).hexdigest()[:16]}"
                    if h == reference_id:
                        act = a
                        break
        if act and act.opportunity:
            return act.opportunity.order, act.opportunity, act

    # 4. Strategy: Match by provider_order_id
    if provider_order_id:
        ord_query = (
            select(Order)
            .where(Order.merchant_id == merchant_id, Order.provider_order_id == provider_order_id)
            .with_for_update()
        )
        ord_res = await db.execute(ord_query)
        order = ord_res.scalar_one_or_none()
        if order:
            opp_query = (
                select(RecoveryOpportunity)
                .where(RecoveryOpportunity.order_id == order.id)
                .options(selectinload(RecoveryOpportunity.actions))
                .with_for_update()
            )
            opp_res = await db.execute(opp_query)
            opp = opp_res.scalar_one_or_none()
            act = opp.actions[-1] if opp and opp.actions else None
            return order, opp, act

    # 5. Strategy: Match by provider_payment_id
    if provider_payment_id:
        att_query = (
            select(PaymentAttempt)
            .where(PaymentAttempt.provider_payment_id == provider_payment_id)
            .with_for_update()
        )
        att_res = await db.execute(att_query)
        att = att_res.scalar_one_or_none()
        if att and att.order_id:
            ord_query = select(Order).where(Order.id == att.order_id).with_for_update()
            ord_res = await db.execute(ord_query)
            order = ord_res.scalar_one_or_none()
            if order:
                opp_query = (
                    select(RecoveryOpportunity)
                    .where(RecoveryOpportunity.order_id == order.id)
                    .options(selectinload(RecoveryOpportunity.actions))
                    .with_for_update()
                )
                opp_res = await db.execute(opp_query)
                opp = opp_res.scalar_one_or_none()
                act = opp.actions[-1] if opp and opp.actions else None
                return order, opp, act

    return None, None, None

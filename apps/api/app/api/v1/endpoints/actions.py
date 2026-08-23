import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import RecoveryAction, RecoveryOpportunity, Order

router = APIRouter(prefix="/actions", tags=["Recovery Actions"])


class ActionListItem(BaseModel):
    id: str
    opportunity_id: str
    order_id: Optional[str]
    order_amount_inr: Optional[float]
    action_type: str
    idempotency_key: str
    policy_approved: bool
    execution_status: str
    provider_action_id: Optional[str]
    payment_link_url: Optional[str]
    error_category: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[ActionListItem])
async def list_actions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Lists all historical and active recovery actions with idempotency and audit details."""
    query = (
        select(RecoveryAction, RecoveryOpportunity, Order)
        .join(RecoveryOpportunity, RecoveryAction.opportunity_id == RecoveryOpportunity.id)
        .join(Order, RecoveryOpportunity.order_id == Order.id)
        .order_by(RecoveryAction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(query)
    rows = res.all()

    items = []
    for action, opp, order in rows:
        items.append(
            ActionListItem(
                id=str(action.id),
                opportunity_id=str(opp.id),
                order_id=str(order.id) if order else None,
                order_amount_inr=float(order.amount_inr) if order else None,
                action_type=action.action_type.value if hasattr(action.action_type, "value") else str(action.action_type),
                idempotency_key=action.idempotency_key,
                policy_approved=action.policy_approved,
                execution_status=action.execution_status.value if hasattr(action.execution_status, "value") else str(action.execution_status),
                provider_action_id=action.provider_action_id,
                payment_link_url=action.payment_link_url,
                error_category=action.error_category,
                error_message=action.error_message,
                created_at=action.created_at.isoformat() if action.created_at else "",
                completed_at=action.completed_at.isoformat() if action.completed_at else None,
            )
        )
    return items

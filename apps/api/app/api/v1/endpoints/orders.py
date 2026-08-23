import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.order import OrderDetailRead
from app.schemas.payment_attempt import PaymentAttemptRead
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve canonical order details including customer and payment attempts history."""
    order = await OrderService.get_by_id(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )
    return order


@router.get("/{order_id}/payment-attempts", response_model=list[PaymentAttemptRead])
async def get_order_payment_attempts(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all payment attempts associated with a specific canonical order."""
    # Ensure order exists
    order = await OrderService.get_by_id(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )
    attempts = await OrderService.get_payment_attempts_by_order(db, order_id=order_id)
    return attempts

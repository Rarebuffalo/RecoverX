import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.order import Order
from app.models.payment_attempt import PaymentAttempt


class OrderService:
    @staticmethod
    async def get_by_id(
        db: AsyncSession, order_id: uuid.UUID, merchant_id: uuid.UUID | None = None
    ) -> Order | None:
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.payment_attempts),
            )
        )
        if merchant_id:
            query = query.where(Order.merchant_id == merchant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_payment_attempts_by_order(
        db: AsyncSession, order_id: uuid.UUID, merchant_id: uuid.UUID | None = None
    ) -> list[PaymentAttempt]:
        query = (
            select(PaymentAttempt)
            .where(PaymentAttempt.order_id == order_id)
            .order_by(PaymentAttempt.created_at.asc())
        )
        if merchant_id:
            query = query.where(PaymentAttempt.merchant_id == merchant_id)
        result = await db.execute(query)
        return list(result.scalars().all())

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.merchant import Merchant


class MerchantService:
    @staticmethod
    async def get_by_id(db: AsyncSession, merchant_id: uuid.UUID) -> Merchant | None:
        query = (
            select(Merchant)
            .where(Merchant.id == merchant_id)
            .options(selectinload(Merchant.policy))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Merchant | None:
        query = select(Merchant).where(Merchant.email == email).options(selectinload(Merchant.policy))
        result = await db.execute(query)
        return result.scalar_one_or_none()

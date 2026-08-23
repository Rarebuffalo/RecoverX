import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.merchant import MerchantRead
from app.services.merchant_service import MerchantService

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("/{merchant_id}", response_model=MerchantRead)
async def get_merchant(
    merchant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve merchant details by ID along with their configured policy."""
    merchant = await MerchantService.get_by_id(db, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with ID {merchant_id} not found.",
        )
    return merchant

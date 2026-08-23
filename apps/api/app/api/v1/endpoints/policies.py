from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import MerchantPolicy, Merchant

router = APIRouter(prefix="/policies", tags=["Merchant Policies"])


class PolicyRead(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    auto_recovery_enabled: bool
    policy_version: str
    max_retry_attempts: int
    cooldown_minutes: int
    max_auto_recovery_amount_inr: float
    min_score_threshold: int
    allowed_actions: List[str]

    class Config:
        from_attributes = True


class PolicyUpdateRequest(BaseModel):
    auto_recovery_enabled: Optional[bool] = None
    policy_version: Optional[str] = None
    max_retry_attempts: Optional[int] = None
    cooldown_minutes: Optional[int] = None
    max_auto_recovery_amount_inr: Optional[float] = None
    min_score_threshold: Optional[int] = None


@router.get("", response_model=PolicyRead)
async def get_active_policy(db: AsyncSession = Depends(get_db)):
    """Fetches the active merchant policy."""
    query = select(MerchantPolicy, Merchant).join(Merchant, MerchantPolicy.merchant_id == Merchant.id).limit(1)
    res = await db.execute(query)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="No merchant policy configured.")
    policy, merchant = row

    return PolicyRead(
        id=str(policy.id),
        merchant_id=str(merchant.id),
        merchant_name=merchant.name,
        auto_recovery_enabled=policy.auto_recovery_enabled,
        policy_version=getattr(policy, "policy_version", "v1"),
        max_retry_attempts=policy.max_retry_attempts,
        cooldown_minutes=policy.cooldown_minutes,
        max_auto_recovery_amount_inr=float(policy.max_auto_recovery_amount_inr),
        min_score_threshold=60,
        allowed_actions=policy.allowed_actions,
    )


@router.put("", response_model=PolicyRead)
async def update_active_policy(
    req: PolicyUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Updates active merchant safety thresholds and policy configuration."""
    query = select(MerchantPolicy, Merchant).join(Merchant, MerchantPolicy.merchant_id == Merchant.id).limit(1)
    res = await db.execute(query)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="No merchant policy found.")
    policy, merchant = row

    if req.auto_recovery_enabled is not None:
        policy.auto_recovery_enabled = req.auto_recovery_enabled
    if req.max_retry_attempts is not None:
        policy.max_retry_attempts = req.max_retry_attempts
    if req.cooldown_minutes is not None:
        policy.cooldown_minutes = req.cooldown_minutes
    if req.max_auto_recovery_amount_inr is not None:
        policy.max_auto_recovery_amount_inr = req.max_auto_recovery_amount_inr

    await db.commit()
    await db.refresh(policy)

    return PolicyRead(
        id=str(policy.id),
        merchant_id=str(merchant.id),
        merchant_name=merchant.name,
        auto_recovery_enabled=policy.auto_recovery_enabled,
        policy_version=getattr(policy, "policy_version", "v1"),
        max_retry_attempts=policy.max_retry_attempts,
        cooldown_minutes=policy.cooldown_minutes,
        max_auto_recovery_amount_inr=float(policy.max_auto_recovery_amount_inr),
        min_score_threshold=req.min_score_threshold or 60,
        allowed_actions=policy.allowed_actions,
    )

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import AuditEvent

router = APIRouter(prefix="/audit-events", tags=["Audit Log"])


class AuditEventItem(BaseModel):
    id: str
    merchant_id: Optional[str]
    opportunity_id: Optional[str]
    event_type: str
    event_summary: str
    actor_type: str
    actor_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[AuditEventItem])
async def list_audit_events(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Returns the immutable append-only audit trail."""
    query = (
        select(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(query)
    events = res.scalars().all()

    return [
        AuditEventItem(
            id=str(e.id),
            merchant_id=str(e.merchant_id) if e.merchant_id else None,
            opportunity_id=str(e.opportunity_id) if e.opportunity_id else None,
            event_type=e.event_type,
            event_summary=e.event_summary,
            actor_type=e.actor_type.value if hasattr(e.actor_type, "value") else str(e.actor_type),
            actor_id="system",
            details=e.event_data,
            created_at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in events
    ]

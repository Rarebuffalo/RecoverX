from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/agent", tags=["Agent Daemon"])


@router.api_route("/checkin", methods=["GET", "POST"])
async def agent_checkin(
    device_id: Optional[str] = Query(None),
    request: Request = None,
) -> Dict[str, Any]:
    """Agent / IDE background liveness checkin endpoint."""
    return {
        "status": "ok",
        "device_id": device_id,
        "message": "RecoverX agent checkin acknowledged.",
    }


@router.api_route("/heartbeat", methods=["GET", "POST"])
async def agent_heartbeat(
    device_id: Optional[str] = Query(None),
    request: Request = None,
) -> Dict[str, Any]:
    """Agent / IDE background heartbeat endpoint."""
    return {
        "status": "ok",
        "device_id": device_id,
        "message": "RecoverX agent heartbeat acknowledged.",
    }

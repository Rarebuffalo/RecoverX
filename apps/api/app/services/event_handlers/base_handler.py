from abc import ABC, abstractmethod
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession


class BaseEventHandler(ABC):
    """Abstract base class for all domain webhook event processors."""

    @abstractmethod
    async def handle(
        self,
        db: AsyncSession,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        account_id: str | None = None,
    ) -> Dict[str, Any]:
        """Executes domain synchronization for the specific event type."""
        pass

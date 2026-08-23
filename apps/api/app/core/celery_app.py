import asyncio
import uuid
from celery import Celery
from app.core.config import settings
from app.core.logging import logger

celery_app = Celery(
    "recoverx_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,  # 30 seconds max task execution
)


@celery_app.task(bind=True, max_retries=1)
def execute_recovery_action_task(self, action_id_str: str):
    """Celery background task for asynchronous recovery action execution."""
    from app.db.session import AsyncSessionLocal
    from app.services.executor.action_executor_service import ActionExecutorService

    async def _run():
        async with AsyncSessionLocal() as db:
            action_id = uuid.UUID(action_id_str)
            action, result = await ActionExecutorService.execute_action(db, action_id)
            return {
                "action_id": str(action.id),
                "status": action.execution_status.value,
                "provider_action_id": action.provider_action_id,
                "payment_link_url": action.payment_link_url,
            }

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(_run())
        else:
            return loop.run_until_complete(_run())
    except Exception as exc:
        logger.error("Celery task execution failed", action_id=action_id_str, error=str(exc))
        raise exc

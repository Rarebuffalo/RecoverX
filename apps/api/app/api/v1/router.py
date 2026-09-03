from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    merchants,
    orders,
    opportunities,
    webhooks,
    developer,
    actions,
    audit_events,
    analytics,
    policies,
    agent,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(agent.router)
api_router.include_router(merchants.router)
api_router.include_router(orders.router)
api_router.include_router(opportunities.router)
api_router.include_router(actions.router)
api_router.include_router(audit_events.router)
api_router.include_router(analytics.router)
api_router.include_router(policies.router)
api_router.include_router(webhooks.router)
api_router.include_router(developer.router)

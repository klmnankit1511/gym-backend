from fastapi import APIRouter
from app.api.v1 import auth, dashboard, members, plans, settings

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(members.router)
api_router.include_router(plans.router)
api_router.include_router(settings.router)

__all__ = ["api_router"]

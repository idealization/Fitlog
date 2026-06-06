from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.recommendations import router as recommendations_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])


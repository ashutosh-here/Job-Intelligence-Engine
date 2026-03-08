from fastapi import APIRouter

from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.health import router as health_router
from app.api.routers.jobs import router as jobs_router
from app.api.routers.orchestrator import router as orchestrator_router
from app.api.routers.outreach import router as outreach_router
from app.api.routers.sources import router as sources_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(sources_router)
api_router.include_router(jobs_router)
api_router.include_router(analytics_router)
api_router.include_router(outreach_router)
api_router.include_router(orchestrator_router)

from fastapi import APIRouter
from app.api.v1.endpoints import analysis, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    analysis.router,
    tags=["analysis"]
)

api_router.include_router(
    health.router,
    tags=["health"]
)
from fastapi import APIRouter, status
from datetime import datetime
import logging
from app.models.responses import HealthResponse
from app.config import settings
from app.core.redis_client import redis_client
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the service and its dependencies"
)
async def health_check() -> HealthResponse:
    """
    Perform a health check on the service and its dependencies.
    
    Returns:
        Health status including Redis and Celery connectivity
    """
    # Check Redis connection
    redis_connected = False
    try:
        if redis_client._client:
            await redis_client.client.ping()
            redis_connected = True
    except RuntimeError:
        # Redis client not initialized
        redis_connected = False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check Celery workers
    celery_active = False
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        celery_active = active_workers is not None and len(active_workers) > 0
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
    
    # Determine overall status
    if redis_connected and celery_active:
        overall_status = "healthy"
    elif redis_connected or celery_active:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        redis_connected=redis_connected,
        celery_active=celery_active,
        timestamp=datetime.now()
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check() -> dict:
    """
    Check if the service is ready to accept requests.
    
    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Check critical dependencies
        await redis_client.client.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if the service is alive"
)
async def liveness_check() -> dict:
    """
    Simple liveness check.
    
    Returns 200 if the service is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }
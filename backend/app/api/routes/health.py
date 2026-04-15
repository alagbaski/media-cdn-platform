"""Health-check routes."""

from fastapi import APIRouter, status

from app.core.config import settings
from app.models.health import HealthResponse, ReadinessResponse
from app.services.storage import is_storage_available

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Liveness probe endpoint used by load balancers and orchestrators."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadinessResponse:
    """Readiness probe endpoint that checks application dependencies."""
    storage_ok = is_storage_available()
    checks = {"storage": "available" if storage_ok else "unavailable"}
    overall = "ok" if storage_ok else "degraded"

    return ReadinessResponse(
        status=overall,
        checks=checks,
        version=settings.app_version,
    )

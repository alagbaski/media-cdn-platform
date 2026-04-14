"""Health-check routes."""

from fastapi import APIRouter, Request, status

from app.core.config import settings
from app.core.logging import get_logger
from app.models.health import HealthResponse, ReadinessResponse

logger = get_logger(__name__)

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
async def readiness_check(request: Request) -> ReadinessResponse:
    """Readiness probe endpoint that checks application dependencies."""
    checks: dict[str, str] = {}

    # Check MinIO storage connectivity
    storage = getattr(request.app.state, "storage", None)
    if storage is None:
        checks["storage"] = "unavailable"
    else:
        try:
            storage._client.bucket_exists(storage.bucket_name)
            checks["storage"] = "ok"
        except Exception as exc:
            logger.warning("Storage readiness check failed: %s", exc)
            checks["storage"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    overall = "ok" if all_ok else "degraded"

    return ReadinessResponse(
        status=overall,
        checks=checks,
        version=settings.app_version,
    )

"""Health response models."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Payload returned by the liveness endpoint."""

    status: Literal["ok", "degraded", "error"]
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """Payload returned by the readiness endpoint, including dependency checks."""

    status: Literal["ok", "degraded", "error"]
    checks: dict[str, str]
    version: str

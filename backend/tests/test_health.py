"""Tests for health and readiness endpoints."""

from fastapi import status
import pytest


@pytest.mark.anyio
async def test_liveness_check(client):
    """Test the liveness endpoint (/health/live)."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


@pytest.mark.anyio
async def test_base_health_check(client):
    """Test the base health endpoint (/health/)."""
    response = await client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_readiness_check_success(client):
    """Test readiness endpoint when storage is available."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["storage"] == "available"


@pytest.mark.anyio
async def test_readiness_check_degraded(client, monkeypatch):
    """Test readiness endpoint when storage is unavailable."""
    monkeypatch.setattr(
        "app.api.routes.health.is_storage_available",
        lambda: False,
    )
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["storage"] == "unavailable"

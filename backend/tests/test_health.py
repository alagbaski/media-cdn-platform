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
async def test_readiness_check_success(client, mock_storage):
    """Test the readiness endpoint when storage is healthy."""
    mock_storage._client.bucket_exists.return_value = True
    
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["storage"] == "ok"


@pytest.mark.anyio
async def test_readiness_check_degraded(client, mock_storage):
    """Test the readiness endpoint when storage fails."""
    mock_storage._client.bucket_exists.side_effect = Exception("Connection error")
    
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["storage"] == "error"

"""Tests for media upload and retrieval endpoints."""

import io

from fastapi import status
import pytest


@pytest.mark.anyio
async def test_upload_media_success(client):
    """Test successful media upload."""
    file_content = b"fake image data"
    file_name = "test.jpg"
    files = {"file": (file_name, io.BytesIO(file_content), "image/jpeg")}
    
    response = await client.post("/api/v1/media/upload", files=files)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["filename"] == "test.jpg"
    assert data["url"] == "/media/test.jpg"


@pytest.mark.anyio
async def test_upload_media_no_filename(client):
    """Test upload error when filename is missing."""
    files = {"file": ("", io.BytesIO(b"data"), "image/jpeg")}
    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_upload_media_empty_file(client):
    """Test upload error for zero-byte files."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_list_media_success(client):
    """Test listing media files."""
    files = {"file": ("image1.png", io.BytesIO(b"img"), "image/png")}
    await client.post("/api/v1/media/upload", files=files)
    response = await client.get("/api/v1/media/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert {"filename": "image1.png"} in data

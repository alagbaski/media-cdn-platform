"""Tests for media upload and retrieval endpoints."""

import io
from fastapi import status


def test_upload_media_success(client, mock_storage):
    """Test successful media upload."""
    file_content = b"fake image data"
    file_name = "test.jpg"
    files = {"file": (file_name, io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post("/api/v1/media/upload", files=files)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["object_name"] == "test.jpg"
    assert "url" in data
    assert data["content_type"] == "image/jpeg"
    assert data["size"] == len(file_content)
    
    # Verify mock was called
    mock_storage.upload_file.assert_called_once()
    mock_storage.get_file_url.assert_called_once_with("test.jpg")


def test_upload_media_no_filename(client):
    """Test upload error when filename is missing."""
    files = {"file": ("", io.BytesIO(b"data"), "image/jpeg")}
    response = client.post("/api/v1/media/upload", files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()


def test_upload_media_empty_file(client):
    """Test upload error for zero-byte files."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = client.post("/api/v1/media/upload", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


def test_list_media_success(client, mock_storage):
    """Test listing media files."""
    # Mock return value for list_objects
    mock_obj = MagicMock()
    mock_obj.object_name = "image1.png"
    mock_obj.size = 1024
    mock_obj.content_type = "image/png"
    mock_obj.last_modified = None
    
    mock_storage._client.list_objects.return_value = [mock_obj]
    
    response = client.get("/api/v1/media/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["object_name"] == "image1.png"

# Need to import MagicMock for the test above
from unittest.mock import MagicMock

"""Test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import create_app
from app.core.config import get_settings
from app.services.storage import StorageService


@pytest.fixture(scope="session")
def settings():
    """Return test settings."""
    return get_settings()


@pytest.fixture
def mock_storage():
    """Mock StorageService for testing."""
    # Use a mock that doesn't strictly enforce a spec for internal attributes like _client
    mock = MagicMock()
    mock.bucket_name = "test-bucket"
    mock._endpoint = "localhost:9000"
    mock._secure = False
    
    # Setup common return values
    mock.get_file_url.return_value = "http://localhost:9000/test-bucket/test.jpg"
    mock.upload_file.return_value = "test.jpg"
    
    # Setup the internal MinIO client mock
    mock._client = MagicMock()
    return mock


@pytest.fixture
def client(mock_storage):
    """Return a TestClient for the FastAPI application."""
    app = create_app()
    
    with TestClient(app) as c:
        # Inject the mock AFTER the lifespan has run to prevent it from being overwritten
        c.app.state.storage = mock_storage
        yield c

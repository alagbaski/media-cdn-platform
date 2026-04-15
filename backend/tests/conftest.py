"""Test fixtures and configuration."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock

from app.main import create_app
from app.core.config import get_settings


@pytest.fixture(scope="session")
def settings():
    """Return test settings."""
    return get_settings()


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio-marked tests."""
    return "asyncio"


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
async def client(mock_storage):
    """Return an AsyncClient for the FastAPI application."""
    app = create_app(initialize_storage=False)
    app.state.storage = mock_storage

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c

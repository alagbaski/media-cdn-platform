"""Test fixtures and configuration."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.config import get_settings
from app.services import storage as storage_service


@pytest.fixture(scope="session")
def settings():
    """Return test settings."""
    return get_settings()


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio-marked tests."""
    return "asyncio"


@pytest.fixture
def temp_storage_dir(tmp_path, monkeypatch):
    """Use isolated temp storage directory for each test."""
    upload_dir = Path(tmp_path) / "storage" / "uploads"
    monkeypatch.setattr(storage_service, "STORAGE_UPLOAD_DIR", upload_dir)
    return upload_dir


@pytest.fixture
async def client(temp_storage_dir):
    """Return an AsyncClient for the FastAPI application."""
    app = create_app(initialize_storage=True)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c

"""Pytest configuration and shared fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.database.db import dispose_engine


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Ensure settings cache is cleared between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Provide isolated settings for tests."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cttel_dollar_bot_test",
    )
    monkeypatch.setenv("PAPER_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncClient:
    """Async HTTP client for FastAPI application."""
    from app.main import create_app

    application = create_app()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await dispose_engine()

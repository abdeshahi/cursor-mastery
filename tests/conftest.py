"""Pytest configuration and shared fixtures."""

import os
import subprocess
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.db import create_engine, dispose_engine, get_session_factory
from app.models.market import MarketPrice, MarketSourceHealth

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/cttel_dollar_bot_test"


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Ensure settings cache is cleared between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Provide isolated settings for tests."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("PAPER_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="session")
def prepare_test_database() -> None:
    """Ensure test database exists and schema is migrated."""
    create_db_cmd = [
        "psql",
        "-h",
        "localhost",
        "-U",
        "postgres",
        "-d",
        "postgres",
        "-tc",
        "SELECT 1 FROM pg_database WHERE datname = 'cttel_dollar_bot_test'",
    ]
    env = {**os.environ, "PGPASSWORD": "postgres"}
    result = subprocess.run(create_db_cmd, capture_output=True, text=True, env=env, check=False)
    if result.stdout.strip() != "1":
        subprocess.run(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "postgres",
                "-d",
                "postgres",
                "-c",
                "CREATE DATABASE cttel_dollar_bot_test OWNER postgres;",
            ],
            env=env,
            check=True,
        )

    migrate_env = {**os.environ, "DATABASE_URL": TEST_DATABASE_URL}
    subprocess.run(
        ["python3", "-m", "alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=migrate_env,
        check=True,
    )


@pytest.fixture
async def db_session(test_settings: Settings, prepare_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session with cleanup after each test."""
    await dispose_engine()
    create_engine(test_settings)
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
        await session.execute(delete(MarketPrice))
        await session.execute(delete(MarketSourceHealth))
        await session.commit()
    await dispose_engine()


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncClient:
    """Async HTTP client for FastAPI application."""
    from app.main import create_app

    application = create_app()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await dispose_engine()

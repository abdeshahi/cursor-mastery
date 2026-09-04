"""Tests for application configuration."""

import pytest

from app.core.config import Settings, get_settings


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PAPER_MODE", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cttel_dollar_bot",
    )
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.paper_mode is True
    assert settings.timezone == "Asia/Tehran"
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_paper_mode_cannot_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAPER_MODE", "false")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cttel_dollar_bot",
    )
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PAPER_MODE must remain true"):
        get_settings()


def test_invalid_database_url_rejected() -> None:
    with pytest.raises(ValueError, match="postgresql\\+asyncpg"):
        Settings(database_url="postgresql://user:pass@localhost/db")

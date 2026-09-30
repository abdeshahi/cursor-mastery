import pytest
import pytest_asyncio

from app.storage.db import Database
from app.storage.settings_repository import SettingsRepository


@pytest_asyncio.fixture
async def settings_repo(tmp_path):
    db = Database(str(tmp_path / 'settings.db'))
    conn = await db.connect()
    repo = SettingsRepository(conn)
    yield repo
    await conn.close()


@pytest.mark.asyncio
async def test_theme_setting(settings_repo: SettingsRepository) -> None:
    assert await settings_repo.get_theme_id() == 'modern'
    await settings_repo.set_theme_id('warm')
    assert await settings_repo.get_theme_id() == 'warm'
    theme = await settings_repo.get_theme()
    assert theme.id == 'warm'

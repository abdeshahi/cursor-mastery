from __future__ import annotations

import aiosqlite

from app.ui.themes import DEFAULT_THEME_ID, get_theme

THEME_SETTING_KEY = 'ui_theme'


class SettingsRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn
        self._theme_cache: str | None = None

    async def get_theme_id(self) -> str:
        if self._theme_cache:
            return self._theme_cache
        cursor = await self.conn.execute(
            'SELECT value FROM shop_settings WHERE key = ?',
            (THEME_SETTING_KEY,),
        )
        row = await cursor.fetchone()
        theme_id = row['value'] if row else DEFAULT_THEME_ID
        self._theme_cache = theme_id
        return theme_id

    async def get_theme(self):
        return get_theme(await self.get_theme_id())

    async def set_theme_id(self, theme_id: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO shop_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (THEME_SETTING_KEY, theme_id),
        )
        await self.conn.commit()
        self._theme_cache = theme_id

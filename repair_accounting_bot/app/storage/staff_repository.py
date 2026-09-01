from __future__ import annotations

from typing import Any

import aiosqlite

from app.config import settings


class StaffRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def seed_from_env(self) -> None:
        admin_ids = settings.admin_user_ids()
        allowed_ids = settings.allowed_user_ids()
        for user_id in allowed_ids:
            is_admin = 1 if user_id in admin_ids else 0
            await self.conn.execute(
                """
                INSERT INTO staff (telegram_id, name, is_admin, active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    is_admin = MAX(staff.is_admin, excluded.is_admin),
                    active = 1
                """,
                (user_id, f'کاربر {user_id}', is_admin),
            )
        await self.conn.commit()

    async def is_active_staff(self, telegram_id: int) -> bool:
        cursor = await self.conn.execute(
            'SELECT 1 FROM staff WHERE telegram_id = ? AND active = 1',
            (telegram_id,),
        )
        return await cursor.fetchone() is not None

    async def is_admin(self, telegram_id: int) -> bool:
        cursor = await self.conn.execute(
            'SELECT is_admin FROM staff WHERE telegram_id = ? AND active = 1',
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return bool(row and row['is_admin'])

    async def add_staff(self, telegram_id: int, name: str, *, is_admin: bool = False) -> None:
        await self.conn.execute(
            """
            INSERT INTO staff (telegram_id, name, is_admin, active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET
                name = excluded.name,
                is_admin = MAX(staff.is_admin, excluded.is_admin),
                active = 1
            """,
            (telegram_id, name.strip(), 1 if is_admin else 0),
        )
        await self.conn.commit()

    async def remove_staff(self, telegram_id: int) -> bool:
        cursor = await self.conn.execute(
            'UPDATE staff SET active = 0 WHERE telegram_id = ? AND active = 1',
            (telegram_id,),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def list_staff(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT telegram_id, name, is_admin, active, added_at
            FROM staff
            WHERE active = 1
            ORDER BY is_admin DESC, name
            """,
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def active_staff_count(self) -> int:
        cursor = await self.conn.execute('SELECT COUNT(*) AS c FROM staff WHERE active = 1')
        row = await cursor.fetchone()
        return int(row['c'] or 0)

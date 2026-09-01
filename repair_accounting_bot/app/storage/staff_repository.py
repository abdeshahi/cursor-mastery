from __future__ import annotations

from typing import Any

import aiosqlite

from app.config import settings
from app.staff.roles import MANAGEABLE_ROLES, ROLE_ADMIN, ROLE_FULL, normalize_role


class StaffRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def seed_from_env(self) -> None:
        admin_ids = settings.admin_user_ids()
        allowed_ids = settings.allowed_user_ids()
        for user_id in allowed_ids:
            role = ROLE_ADMIN if user_id in admin_ids else ROLE_FULL
            is_admin = 1 if role == ROLE_ADMIN else 0
            await self.conn.execute(
                """
                INSERT INTO staff (telegram_id, name, is_admin, role, active)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    is_admin = MAX(staff.is_admin, excluded.is_admin),
                    role = CASE
                        WHEN excluded.is_admin = 1 OR staff.is_admin = 1 THEN ?
                        ELSE staff.role
                    END,
                    active = 1
                """,
                (user_id, f'کاربر {user_id}', is_admin, role, ROLE_ADMIN),
            )
        await self.conn.commit()

    async def get_staff(self, telegram_id: int) -> dict[str, Any] | None:
        cursor = await self.conn.execute(
            'SELECT telegram_id, name, is_admin, role, active, added_at FROM staff WHERE telegram_id = ?',
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def is_active_staff(self, telegram_id: int) -> bool:
        cursor = await self.conn.execute(
            'SELECT 1 FROM staff WHERE telegram_id = ? AND active = 1',
            (telegram_id,),
        )
        return await cursor.fetchone() is not None

    async def get_role(self, telegram_id: int) -> str | None:
        cursor = await self.conn.execute(
            'SELECT role, is_admin FROM staff WHERE telegram_id = ? AND active = 1',
            (telegram_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return normalize_role(row['role'], is_admin=bool(row['is_admin']))

    async def is_admin(self, telegram_id: int) -> bool:
        role = await self.get_role(telegram_id)
        return role == ROLE_ADMIN

    async def add_staff(
        self,
        telegram_id: int,
        name: str,
        *,
        role: str = ROLE_FULL,
        is_admin: bool = False,
    ) -> None:
        role = normalize_role(role, is_admin=is_admin)
        await self.conn.execute(
            """
            INSERT INTO staff (telegram_id, name, is_admin, role, active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET
                name = excluded.name,
                is_admin = MAX(staff.is_admin, excluded.is_admin),
                role = CASE
                    WHEN staff.is_admin = 1 THEN ?
                    WHEN excluded.is_admin = 1 THEN ?
                    ELSE excluded.role
                END,
                active = 1
            """,
            (
                telegram_id,
                name.strip(),
                1 if role == ROLE_ADMIN else 0,
                role,
                ROLE_ADMIN,
                ROLE_ADMIN,
            ),
        )
        await self.conn.commit()

    async def set_role(self, telegram_id: int, role: str) -> bool:
        role = normalize_role(role)
        if role == ROLE_ADMIN:
            is_admin = 1
        else:
            is_admin = 0
        cursor = await self.conn.execute(
            """
            UPDATE staff
            SET role = ?, is_admin = ?
            WHERE telegram_id = ? AND active = 1
            """,
            (role, is_admin, telegram_id),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def set_name(self, telegram_id: int, name: str) -> bool:
        cursor = await self.conn.execute(
            'UPDATE staff SET name = ? WHERE telegram_id = ? AND active = 1',
            (name.strip(), telegram_id),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

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
            SELECT telegram_id, name, is_admin, role, active, added_at
            FROM staff
            WHERE active = 1
            ORDER BY is_admin DESC, name
            """,
        )
        rows = [dict(row) for row in await cursor.fetchall()]
        for row in rows:
            row['role'] = normalize_role(row['role'], is_admin=bool(row['is_admin']))
        return rows

    async def active_staff_count(self) -> int:
        cursor = await self.conn.execute('SELECT COUNT(*) AS c FROM staff WHERE active = 1')
        row = await cursor.fetchone()
        return int(row['c'] or 0)

    async def create_invite(self, created_by: int, role: str, *, max_uses: int = 1) -> str:
        from app.bot.invite_utils import new_invite_token

        role = normalize_role(role)
        if role not in MANAGEABLE_ROLES:
            role = ROLE_FULL
        token = new_invite_token()
        await self.conn.execute(
            """
            INSERT INTO staff_invites (token, role, created_by, max_uses, use_count, active)
            VALUES (?, ?, ?, ?, 0, 1)
            """,
            (token, role, created_by, max_uses),
        )
        await self.conn.commit()
        return token

    async def list_invites(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        query = """
            SELECT token, role, created_by, max_uses, use_count, active, created_at
            FROM staff_invites
        """
        if active_only:
            query += ' WHERE active = 1'
        query += ' ORDER BY created_at DESC'
        cursor = await self.conn.execute(query)
        rows = [dict(row) for row in await cursor.fetchall()]
        for row in rows:
            row['role'] = normalize_role(row['role'])
        return rows

    async def revoke_invite(self, token: str) -> bool:
        cursor = await self.conn.execute(
            'UPDATE staff_invites SET active = 0 WHERE token = ? AND active = 1',
            (token,),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def try_redeem_invite(self, token: str, telegram_id: int, name: str) -> str | None:
        if await self.is_active_staff(telegram_id):
            return None

        cursor = await self.conn.execute(
            """
            SELECT token, role, max_uses, use_count, active
            FROM staff_invites
            WHERE token = ?
            """,
            (token,),
        )
        invite = await cursor.fetchone()
        if not invite or not invite['active']:
            return '⛔️ لینک دعوت نامعتبر یا لغو شده است.'
        if invite['max_uses'] > 0 and invite['use_count'] >= invite['max_uses']:
            return '⛔️ این لینک دعوت قبلاً استفاده شده است.'

        role = normalize_role(invite['role'])
        if role not in MANAGEABLE_ROLES:
            role = ROLE_FULL

        await self.add_staff(telegram_id, name, role=role)
        new_count = int(invite['use_count']) + 1
        deactivate = invite['max_uses'] > 0 and new_count >= invite['max_uses']
        await self.conn.execute(
            """
            UPDATE staff_invites
            SET use_count = ?, active = ?
            WHERE token = ?
            """,
            (new_count, 0 if deactivate else 1, token),
        )
        await self.conn.commit()
        return None

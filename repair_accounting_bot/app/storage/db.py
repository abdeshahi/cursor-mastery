from __future__ import annotations

import aiosqlite
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    default_pct REAL NOT NULL DEFAULT 40,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    technician_id INTEGER REFERENCES technicians(id),
    device TEXT NOT NULL DEFAULT '',
    issue TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    labor_amount INTEGER NOT NULL DEFAULT 0,
    technician_pct REAL NOT NULL DEFAULT 40,
    parts_cost INTEGER NOT NULL DEFAULT 0,
    parts_sell INTEGER NOT NULL DEFAULT 0,
    customer_paid INTEGER NOT NULL DEFAULT 0,
    supplier_paid INTEGER NOT NULL DEFAULT 0,
    technician_paid INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS repair_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL REFERENCES repairs(id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(id),
    part_name TEXT NOT NULL,
    cost INTEGER NOT NULL DEFAULT 0,
    sell_price INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL REFERENCES repairs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    amount INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_repairs_status ON repairs(status);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);

CREATE TABLE IF NOT EXISTS staff (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    is_admin INTEGER NOT NULL DEFAULT 0,
    role TEXT NOT NULL DEFAULT 'full',
    can_edit_repair INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS staff_invites (
    token TEXT PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'full',
    created_by INTEGER NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 1,
    use_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shop_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def connect(self) -> aiosqlite.Connection:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.executescript(SCHEMA)
        await _migrate(conn)
        await conn.commit()
        return conn


async def _migrate(conn: aiosqlite.Connection) -> None:
    cursor = await conn.execute('PRAGMA table_info(repairs)')
    columns = {row[1] for row in await cursor.fetchall()}
    if 'technician_paid' not in columns:
        await conn.execute(
            'ALTER TABLE repairs ADD COLUMN technician_paid INTEGER NOT NULL DEFAULT 0',
        )

    cursor = await conn.execute('PRAGMA table_info(staff)')
    staff_columns = {row[1] for row in await cursor.fetchall()}
    if staff_columns and 'role' not in staff_columns:
        await conn.execute("ALTER TABLE staff ADD COLUMN role TEXT NOT NULL DEFAULT 'full'")
        await conn.execute("UPDATE staff SET role = 'admin' WHERE is_admin = 1")
        await conn.execute("UPDATE staff SET role = 'full' WHERE is_admin = 0")

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_invites (
            token TEXT PRIMARY KEY,
            role TEXT NOT NULL DEFAULT 'full',
            created_by INTEGER NOT NULL,
            max_uses INTEGER NOT NULL DEFAULT 1,
            use_count INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """,
    )

    if staff_columns and 'can_edit_repair' not in staff_columns:
        await conn.execute(
            'ALTER TABLE staff ADD COLUMN can_edit_repair INTEGER NOT NULL DEFAULT 0',
        )
        await conn.execute(
            """
            UPDATE staff SET can_edit_repair = 1
            WHERE is_admin = 1 OR role IN ('admin', 'full', 'reception')
            """,
        )

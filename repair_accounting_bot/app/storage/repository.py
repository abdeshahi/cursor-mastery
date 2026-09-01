from __future__ import annotations

from typing import Any

import aiosqlite

from app.services.accounting import calculate_repair_totals


class RepairRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def find_or_create_customer(self, name: str, phone: str) -> int:
        cursor = await self.conn.execute(
            'SELECT id FROM customers WHERE phone = ? AND phone != ""',
            (phone,),
        )
        row = await cursor.fetchone()
        if row:
            return int(row['id'])
        cursor = await self.conn.execute(
            'INSERT INTO customers (name, phone) VALUES (?, ?)',
            (name.strip(), phone.strip()),
        )
        await self.conn.commit()
        return int(cursor.lastrowid)

    async def list_technicians(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            'SELECT id, name, default_pct FROM technicians WHERE active = 1 ORDER BY name',
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def add_technician(self, name: str, default_pct: float) -> int:
        cursor = await self.conn.execute(
            'INSERT INTO technicians (name, default_pct) VALUES (?, ?)',
            (name.strip(), default_pct),
        )
        await self.conn.commit()
        return int(cursor.lastrowid)

    async def deactivate_technician(self, tech_id: int) -> bool:
        cursor = await self.conn.execute(
            'UPDATE technicians SET active = 0 WHERE id = ? AND active = 1',
            (tech_id,),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def list_all_technicians(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            'SELECT id, name, default_pct, active FROM technicians ORDER BY active DESC, name',
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def list_suppliers(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            'SELECT id, name FROM suppliers WHERE active = 1 ORDER BY name',
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def add_supplier(self, name: str) -> int:
        cursor = await self.conn.execute(
            'INSERT INTO suppliers (name) VALUES (?)',
            (name.strip(),),
        )
        await self.conn.commit()
        return int(cursor.lastrowid)

    async def deactivate_supplier(self, sup_id: int) -> bool:
        cursor = await self.conn.execute(
            'UPDATE suppliers SET active = 0 WHERE id = ? AND active = 1',
            (sup_id,),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def list_all_suppliers(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            'SELECT id, name, active FROM suppliers ORDER BY active DESC, name',
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def create_repair(
        self,
        *,
        customer_id: int,
        technician_id: int | None,
        device: str,
        issue: str,
        labor_amount: int,
        technician_pct: float,
        parts: list[dict[str, Any]],
        notes: str = '',
    ) -> int:
        parts_cost = sum(int(part['cost']) for part in parts)
        parts_sell = sum(int(part['sell_price']) for part in parts)
        cursor = await self.conn.execute(
            """
            INSERT INTO repairs (
                customer_id, technician_id, device, issue,
                labor_amount, technician_pct, parts_cost, parts_sell, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                technician_id,
                device.strip(),
                issue.strip(),
                labor_amount,
                technician_pct,
                parts_cost,
                parts_sell,
                notes.strip(),
            ),
        )
        repair_id = int(cursor.lastrowid)
        for part in parts:
            await self.conn.execute(
                """
                INSERT INTO repair_parts (repair_id, supplier_id, part_name, cost, sell_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    repair_id,
                    part.get('supplier_id'),
                    part['part_name'],
                    int(part['cost']),
                    int(part['sell_price']),
                ),
            )
        await self.conn.commit()
        return repair_id

    async def get_repair(self, repair_id: int) -> dict[str, Any] | None:
        cursor = await self.conn.execute(
            """
            SELECT r.*, c.name AS customer_name, c.phone AS customer_phone,
                   t.name AS technician_name
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            LEFT JOIN technicians t ON t.id = r.technician_id
            WHERE r.id = ?
            """,
            (repair_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        repair = dict(row)
        repair['parts'] = await self.list_repair_parts(repair_id)
        repair['totals'] = calculate_repair_totals(
            labor_amount=int(repair['labor_amount']),
            parts_cost=int(repair['parts_cost']),
            parts_sell=int(repair['parts_sell']),
            technician_pct=float(repair['technician_pct']),
            customer_paid=int(repair['customer_paid']),
            supplier_paid=int(repair['supplier_paid']),
            technician_paid=int(repair.get('technician_paid') or 0),
        )
        return repair

    async def list_repair_parts(self, repair_id: int) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT rp.*, s.name AS supplier_name
            FROM repair_parts rp
            LEFT JOIN suppliers s ON s.id = rp.supplier_id
            WHERE rp.repair_id = ?
            ORDER BY rp.id
            """,
            (repair_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def summary_report(self) -> dict[str, int]:
        dashboard = await self.accounting_dashboard()
        return {
            'customer_debt': dashboard['customer_debt'],
            'supplier_debt': dashboard['supplier_debt'],
            'technician_share_open': dashboard['technician_share'],
            'shop_profit': dashboard['shop_profit'],
            'open_count': dashboard['open_count'],
        }

    async def accounting_dashboard(self) -> dict[str, Any]:
        cursor = await self.conn.execute(
            """
            SELECT
                COUNT(*) AS open_count,
                COALESCE(SUM(labor_amount + parts_sell - customer_paid), 0) AS customer_debt,
                COALESCE(SUM(parts_cost - supplier_paid), 0) AS supplier_debt,
                COALESCE(SUM(ROUND(labor_amount * technician_pct / 100.0)), 0) AS technician_share,
                COALESCE(SUM(COALESCE(technician_paid, 0)), 0) AS technician_paid,
                COALESCE(SUM(
                    ROUND(labor_amount * technician_pct / 100.0)
                ), 0) - COALESCE(SUM(COALESCE(technician_paid, 0)), 0) AS technician_debt,
                COALESCE(SUM(
                    (labor_amount + parts_sell) - parts_cost - ROUND(labor_amount * technician_pct / 100.0)
                ), 0) AS shop_profit
            FROM repairs
            WHERE status = 'open'
            """,
        )
        totals = dict(await cursor.fetchone())

        cursor = await self.conn.execute(
            """
            SELECT t.name, r.technician_pct AS pct,
                   SUM(ROUND(r.labor_amount * r.technician_pct / 100.0)) AS share,
                   SUM(COALESCE(r.technician_paid, 0)) AS paid,
                   SUM(
                       ROUND(r.labor_amount * r.technician_pct / 100.0)
                   ) - SUM(COALESCE(r.technician_paid, 0)) AS debt
            FROM repairs r
            JOIN technicians t ON t.id = r.technician_id
            WHERE r.status = 'open'
            GROUP BY t.id
            ORDER BY debt DESC
            """,
        )
        technicians = [dict(row) for row in await cursor.fetchall()]

        cursor = await self.conn.execute(
            """
            SELECT COALESCE(s.name, 'بدون فروشنده') AS name,
                   SUM(rp.cost) AS part_cost
            FROM repair_parts rp
            JOIN repairs r ON r.id = rp.repair_id
            LEFT JOIN suppliers s ON s.id = rp.supplier_id
            WHERE r.status = 'open' AND (r.parts_cost - r.supplier_paid) > 0
            GROUP BY COALESCE(s.id, 0), COALESCE(s.name, 'بدون فروشنده')
            ORDER BY part_cost DESC
            """,
        )
        suppliers = [{'name': row['name'], 'debt': int(row['part_cost'] or 0)} for row in await cursor.fetchall()]

        return {
            'open_count': int(totals['open_count'] or 0),
            'customer_debt': int(totals['customer_debt'] or 0),
            'supplier_debt': int(totals['supplier_debt'] or 0),
            'technician_share': int(totals['technician_share'] or 0),
            'technician_paid': int(totals['technician_paid'] or 0),
            'technician_debt': int(totals['technician_debt'] or 0),
            'shop_profit': int(totals['shop_profit'] or 0),
            'technicians': technicians,
            'suppliers': suppliers,
        }

    async def search_repairs(self, query: str, limit: int = 15) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        if query.isdigit():
            cursor = await self.conn.execute(
                """
                SELECT r.id, r.device, r.status, c.name AS customer_name
                FROM repairs r
                JOIN customers c ON c.id = r.customer_id
                WHERE r.id = ?
                """,
                (int(query),),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

        pattern = f'%{query}%'
        cursor = await self.conn.execute(
            """
            SELECT r.id, r.device, r.status, c.name AS customer_name
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE c.name LIKE ? OR c.phone LIKE ? OR r.device LIKE ? OR r.issue LIKE ?
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, pattern, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def list_open_repairs(self, limit: int = 20) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT r.id, r.device, r.status, c.name AS customer_name,
                   r.labor_amount + r.parts_sell AS customer_total,
                   r.customer_paid,
                   r.labor_amount + r.parts_sell - r.customer_paid AS customer_debt
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def list_open_repairs_full(self, limit: int = 200) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT r.id
            FROM repairs r
            WHERE r.status = 'open'
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        repairs: list[dict[str, Any]] = []
        for row in await cursor.fetchall():
            repair = await self.get_repair(int(row['id']))
            if repair:
                repairs.append(repair)
        return repairs

    async def add_customer_payment(self, repair_id: int, amount: int, note: str = '') -> None:
        await self.conn.execute(
            'UPDATE repairs SET customer_paid = customer_paid + ? WHERE id = ?',
            (amount, repair_id),
        )
        await self.conn.execute(
            'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
            (repair_id, 'customer', amount, note),
        )
        await self.conn.commit()

    async def add_supplier_payment(self, repair_id: int, amount: int, note: str = '') -> None:
        await self.conn.execute(
            'UPDATE repairs SET supplier_paid = supplier_paid + ? WHERE id = ?',
            (amount, repair_id),
        )
        await self.conn.execute(
            'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
            (repair_id, 'supplier', amount, note),
        )
        await self.conn.commit()

    async def add_technician_payment(self, repair_id: int, amount: int, note: str = '') -> None:
        await self.conn.execute(
            'UPDATE repairs SET technician_paid = technician_paid + ? WHERE id = ?',
            (amount, repair_id),
        )
        await self.conn.execute(
            'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
            (repair_id, 'technician', amount, note),
        )
        await self.conn.commit()

    async def close_repair(self, repair_id: int) -> None:
        await self.conn.execute(
            "UPDATE repairs SET status = 'closed', closed_at = datetime('now') WHERE id = ?",
            (repair_id,),
        )
        await self.conn.commit()

    async def customer_debts(self, limit: int = 20) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT c.name, c.phone,
                   SUM(r.labor_amount + r.parts_sell - r.customer_paid) AS debt
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
              AND (r.labor_amount + r.parts_sell - r.customer_paid) > 0
            GROUP BY c.id
            ORDER BY debt DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

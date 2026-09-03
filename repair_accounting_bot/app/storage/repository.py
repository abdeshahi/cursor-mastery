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

    async def update_repair_labor(self, repair_id: int, labor_amount: int) -> bool:
        cursor = await self.conn.execute(
            """
            UPDATE repairs SET labor_amount = ?
            WHERE id = ? AND status = 'open'
            """,
            (labor_amount, repair_id),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def add_repair_part(self, repair_id: int, part: dict[str, Any]) -> bool:
        cursor = await self.conn.execute(
            "SELECT id FROM repairs WHERE id = ? AND status = 'open'",
            (repair_id,),
        )
        if not await cursor.fetchone():
            return False
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
        await self.conn.execute(
            """
            UPDATE repairs SET
                parts_cost = parts_cost + ?,
                parts_sell = parts_sell + ?
            WHERE id = ?
            """,
            (int(part['cost']), int(part['sell_price']), repair_id),
        )
        await self.conn.commit()
        return True

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
                SELECT r.id, r.device, r.issue, r.status, c.name AS customer_name, c.phone AS customer_phone
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
            SELECT r.id, r.device, r.issue, r.status, c.name AS customer_name, c.phone AS customer_phone
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

    async def count_repairs(self, status: str | None = None) -> int:
        if status in ('open', 'closed'):
            cursor = await self.conn.execute(
                'SELECT COUNT(*) AS cnt FROM repairs WHERE status = ?',
                (status,),
            )
        else:
            cursor = await self.conn.execute('SELECT COUNT(*) AS cnt FROM repairs')
        row = await cursor.fetchone()
        return int(row['cnt'] or 0)

    async def list_repairs_brief(
        self,
        *,
        status: str | None = 'open',
        limit: int = 15,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if status in ('open', 'closed'):
            where = 'WHERE r.status = ?'
            params: list[Any] = [status]
        else:
            where = ''
            params = []
        params.extend([limit, offset])
        cursor = await self.conn.execute(
            f"""
            SELECT r.id, r.device, r.issue, r.status, r.created_at,
                   r.labor_amount + r.parts_sell AS customer_total,
                   c.name AS customer_name, c.phone AS customer_phone,
                   t.name AS technician_name
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            LEFT JOIN technicians t ON t.id = r.technician_id
            {where}
            ORDER BY r.id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        )
        return [dict(row) for row in await cursor.fetchall()]

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

    async def technicians_with_debt(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT t.id, t.name, r.technician_pct AS pct,
                   SUM(ROUND(r.labor_amount * r.technician_pct / 100.0)) AS share,
                   SUM(COALESCE(r.technician_paid, 0)) AS paid,
                   SUM(ROUND(r.labor_amount * r.technician_pct / 100.0))
                       - SUM(COALESCE(r.technician_paid, 0)) AS debt
            FROM repairs r
            JOIN technicians t ON t.id = r.technician_id
            WHERE r.status = 'open'
            GROUP BY t.id
            HAVING debt > 0
            ORDER BY debt DESC
            """,
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def suppliers_with_debt(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT COALESCE(s.id, 0) AS id,
                   COALESCE(s.name, 'بدون فروشنده') AS name,
                   SUM(rp.cost) AS debt
            FROM repair_parts rp
            JOIN repairs r ON r.id = rp.repair_id
            LEFT JOIN suppliers s ON s.id = rp.supplier_id
            WHERE r.status = 'open' AND (r.parts_cost - r.supplier_paid) > 0
            GROUP BY COALESCE(s.id, 0), COALESCE(s.name, 'بدون فروشنده')
            HAVING debt > 0
            ORDER BY debt DESC
            """,
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def repairs_with_technician_debt(self, technician_id: int) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT r.id, c.name AS customer_name, r.device,
                   ROUND(r.labor_amount * r.technician_pct / 100.0) AS share,
                   COALESCE(r.technician_paid, 0) AS paid,
                   ROUND(r.labor_amount * r.technician_pct / 100.0)
                       - COALESCE(r.technician_paid, 0) AS debt
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
              AND r.technician_id = ?
              AND (
                  ROUND(r.labor_amount * r.technician_pct / 100.0)
                  - COALESCE(r.technician_paid, 0)
              ) > 0
            ORDER BY r.id
            """,
            (technician_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def repairs_with_supplier_debt(self, supplier_id: int) -> list[dict[str, Any]]:
        if supplier_id == 0:
            supplier_filter = 'rp.supplier_id IS NULL'
        else:
            supplier_filter = 'rp.supplier_id = ?'
        params: tuple[Any, ...] = (supplier_id,) if supplier_id else ()
        cursor = await self.conn.execute(
            f"""
            SELECT r.id, c.name AS customer_name, r.device,
                   r.parts_cost - r.supplier_paid AS repair_supplier_debt,
                   SUM(rp.cost) AS supplier_part_cost
            FROM repair_parts rp
            JOIN repairs r ON r.id = rp.repair_id
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
              AND (r.parts_cost - r.supplier_paid) > 0
              AND {supplier_filter}
            GROUP BY r.id
            ORDER BY r.id
            """,
            params,
        )
        rows = []
        for row in await cursor.fetchall():
            item = dict(row)
            item['debt'] = min(
                int(item['repair_supplier_debt'] or 0),
                int(item['supplier_part_cost'] or 0),
            )
            if item['debt'] > 0:
                rows.append(item)
        return rows

    async def allocate_technician_payment(
        self,
        technician_id: int,
        amount: int,
        *,
        repair_id: int | None = None,
    ) -> list[tuple[int, int]]:
        if amount <= 0:
            return []
        if repair_id is not None:
            repairs = await self.repairs_with_technician_debt(technician_id)
            targets = [r for r in repairs if int(r['id']) == repair_id]
        else:
            targets = await self.repairs_with_technician_debt(technician_id)

        remaining = amount
        applied: list[tuple[int, int]] = []
        for row in targets:
            if remaining <= 0:
                break
            pay = min(remaining, int(row['debt']))
            if pay <= 0:
                continue
            await self.conn.execute(
                'UPDATE repairs SET technician_paid = technician_paid + ? WHERE id = ?',
                (pay, int(row['id'])),
            )
            await self.conn.execute(
                'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
                (int(row['id']), 'technician', pay, f'tech:{technician_id}'),
            )
            applied.append((int(row['id']), pay))
            remaining -= pay
        if applied:
            await self.conn.commit()
        return applied

    async def allocate_supplier_payment(
        self,
        supplier_id: int,
        amount: int,
        *,
        repair_id: int | None = None,
    ) -> list[tuple[int, int]]:
        if amount <= 0:
            return []
        if repair_id is not None:
            repairs = await self.repairs_with_supplier_debt(supplier_id)
            targets = [r for r in repairs if int(r['id']) == repair_id]
        else:
            targets = await self.repairs_with_supplier_debt(supplier_id)

        remaining = amount
        applied: list[tuple[int, int]] = []
        for row in targets:
            if remaining <= 0:
                break
            pay = min(remaining, int(row['debt']))
            if pay <= 0:
                continue
            await self.conn.execute(
                'UPDATE repairs SET supplier_paid = supplier_paid + ? WHERE id = ?',
                (pay, int(row['id'])),
            )
            await self.conn.execute(
                'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
                (int(row['id']), 'supplier', pay, f'sup:{supplier_id}'),
            )
            applied.append((int(row['id']), pay))
            remaining -= pay
        if applied:
            await self.conn.commit()
        return applied

    async def customers_with_debt(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT c.id, c.name, c.phone,
                   SUM(r.labor_amount + r.parts_sell - r.customer_paid) AS debt
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
              AND (r.labor_amount + r.parts_sell - r.customer_paid) > 0
            GROUP BY c.id
            HAVING debt > 0
            ORDER BY debt DESC
            """,
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def repairs_with_customer_debt(self, customer_id: int) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT r.id, c.name AS customer_name, r.device,
                   r.labor_amount + r.parts_sell AS customer_total,
                   r.customer_paid,
                   r.labor_amount + r.parts_sell - r.customer_paid AS debt
            FROM repairs r
            JOIN customers c ON c.id = r.customer_id
            WHERE r.status = 'open'
              AND r.customer_id = ?
              AND (r.labor_amount + r.parts_sell - r.customer_paid) > 0
            ORDER BY r.id
            """,
            (customer_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def allocate_customer_payment(
        self,
        customer_id: int,
        amount: int,
        *,
        repair_id: int | None = None,
    ) -> list[tuple[int, int]]:
        if amount <= 0:
            return []
        if repair_id is not None:
            targets = await self.repairs_with_customer_debt(customer_id)
            targets = [r for r in targets if int(r['id']) == repair_id]
        else:
            targets = await self.repairs_with_customer_debt(customer_id)

        remaining = amount
        applied: list[tuple[int, int]] = []
        for row in targets:
            if remaining <= 0:
                break
            pay = min(remaining, int(row['debt']))
            if pay <= 0:
                continue
            await self.conn.execute(
                'UPDATE repairs SET customer_paid = customer_paid + ? WHERE id = ?',
                (pay, int(row['id'])),
            )
            await self.conn.execute(
                'INSERT INTO payments (repair_id, kind, amount, note) VALUES (?, ?, ?, ?)',
                (int(row['id']), 'customer', pay, f'cust:{customer_id}'),
            )
            applied.append((int(row['id']), pay))
            remaining -= pay
        if applied:
            await self.conn.commit()
        return applied

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

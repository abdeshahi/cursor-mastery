from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepairTotals:
    labor_amount: int
    parts_cost: int
    parts_sell: int
    customer_total: int
    customer_paid: int
    customer_debt: int
    supplier_debt: int
    technician_labor_share: int
    technician_parts_share: int
    technician_share: int
    technician_paid: int
    technician_debt: int
    shop_profit: int


def technician_share_sql(prefix: str = '') -> str:
    return (
        f'ROUND({prefix}labor_amount * {prefix}technician_pct / 100.0) + '
        f'ROUND(({prefix}parts_sell - {prefix}parts_cost) * {prefix}technician_pct / 100.0)'
    )


def calculate_technician_shares(
    *,
    labor_amount: int,
    parts_cost: int,
    parts_sell: int,
    technician_pct: float,
) -> tuple[int, int, int]:
    parts_profit = parts_sell - parts_cost
    labor_share = round(labor_amount * technician_pct / 100)
    parts_share = round(parts_profit * technician_pct / 100)
    return labor_share, parts_share, labor_share + parts_share


def calculate_repair_totals(
    *,
    labor_amount: int,
    parts_cost: int,
    parts_sell: int,
    technician_pct: float,
    customer_paid: int,
    supplier_paid: int,
    technician_paid: int = 0,
) -> RepairTotals:
    customer_total = labor_amount + parts_sell
    customer_debt = max(customer_total - customer_paid, 0)
    supplier_debt = max(parts_cost - supplier_paid, 0)
    labor_share, parts_share, technician_share = calculate_technician_shares(
        labor_amount=labor_amount,
        parts_cost=parts_cost,
        parts_sell=parts_sell,
        technician_pct=technician_pct,
    )
    technician_debt = max(technician_share - technician_paid, 0)
    shop_profit = customer_total - parts_cost - technician_share
    return RepairTotals(
        labor_amount=labor_amount,
        parts_cost=parts_cost,
        parts_sell=parts_sell,
        customer_total=customer_total,
        customer_paid=customer_paid,
        customer_debt=customer_debt,
        supplier_debt=supplier_debt,
        technician_labor_share=labor_share,
        technician_parts_share=parts_share,
        technician_share=technician_share,
        technician_paid=technician_paid,
        technician_debt=technician_debt,
        shop_profit=shop_profit,
    )


def format_toman(amount: int) -> str:
    return f'{amount:,} تومان'

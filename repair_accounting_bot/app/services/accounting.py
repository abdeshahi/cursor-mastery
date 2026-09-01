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
    technician_share: int
    shop_profit: int


def calculate_repair_totals(
    *,
    labor_amount: int,
    parts_cost: int,
    parts_sell: int,
    technician_pct: float,
    customer_paid: int,
    supplier_paid: int,
) -> RepairTotals:
    customer_total = labor_amount + parts_sell
    customer_debt = max(customer_total - customer_paid, 0)
    supplier_debt = max(parts_cost - supplier_paid, 0)
    technician_share = round(labor_amount * technician_pct / 100)
    shop_profit = customer_total - parts_cost - technician_share
    return RepairTotals(
        labor_amount=labor_amount,
        parts_cost=parts_cost,
        parts_sell=parts_sell,
        customer_total=customer_total,
        customer_paid=customer_paid,
        customer_debt=customer_debt,
        supplier_debt=supplier_debt,
        technician_share=technician_share,
        shop_profit=shop_profit,
    )


def format_toman(amount: int) -> str:
    return f'{amount:,} تومان'

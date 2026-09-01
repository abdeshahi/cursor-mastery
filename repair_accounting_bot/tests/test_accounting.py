import pytest

from app.services.accounting import calculate_repair_totals


def test_calculate_repair_totals_with_parts_and_debts() -> None:
    totals = calculate_repair_totals(
        labor_amount=500_000,
        parts_cost=300_000,
        parts_sell=450_000,
        technician_pct=40,
        customer_paid=200_000,
        supplier_paid=100_000,
    )
    assert totals.customer_total == 950_000
    assert totals.customer_debt == 750_000
    assert totals.supplier_debt == 200_000
    assert totals.technician_share == 200_000
    assert totals.shop_profit == 450_000


def test_calculate_repair_totals_with_technician_settlement() -> None:
    totals = calculate_repair_totals(
        labor_amount=500_000,
        parts_cost=0,
        parts_sell=0,
        technician_pct=40,
        customer_paid=500_000,
        supplier_paid=0,
        technician_paid=100_000,
    )
    assert totals.technician_share == 200_000
    assert totals.technician_debt == 100_000


def test_calculate_repair_totals_no_debt_when_fully_paid() -> None:
    totals = calculate_repair_totals(
        labor_amount=400_000,
        parts_cost=0,
        parts_sell=0,
        technician_pct=50,
        customer_paid=400_000,
        supplier_paid=0,
    )
    assert totals.customer_debt == 0
    assert totals.technician_share == 200_000
    assert totals.shop_profit == 200_000

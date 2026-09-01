import pytest
import pytest_asyncio

from app.services.formatters import format_accounting_report, format_invoice
from app.storage.db import Database
from app.storage.repository import RepairRepository


@pytest_asyncio.fixture
async def repo(tmp_path):
    db = Database(str(tmp_path / 'test.db'))
    conn = await db.connect()
    repository = RepairRepository(conn)
    tech_id = await repository.add_technician('علی', 40)
    yield repository, tech_id
    await conn.close()


@pytest.mark.asyncio
async def test_create_repair_and_payments(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('رضا', '09120000000')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='iPhone 12',
        issue='تاچ',
        labor_amount=600_000,
        technician_pct=40,
        parts=[{'part_name': 'LCD', 'cost': 2_000_000, 'sell_price': 2_500_000, 'supplier_id': None}],
    )
    repair = await repository.get_repair(repair_id)
    assert repair is not None
    assert repair['totals'].customer_total == 3_100_000
    assert repair['totals'].shop_profit == 860_000

    invoice = format_invoice(repair)
    assert 'فاکتور فروش' in invoice
    assert '3,100,000' in invoice

    await repository.add_technician_payment(repair_id, 100_000)
    repair = await repository.get_repair(repair_id)
    assert repair['totals'].technician_debt == 140_000

    dashboard = await repository.accounting_dashboard()
    report = format_accounting_report(dashboard)
    assert 'سود فروشگاه' in report
    assert dashboard['technician_debt'] == 140_000


@pytest.mark.asyncio
async def test_search_repairs(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('حسین', '09121111111')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='Samsung A54',
        issue='باتری',
        labor_amount=200_000,
        technician_pct=40,
        parts=[],
    )
    by_id = await repository.search_repairs(str(repair_id))
    assert len(by_id) == 1
    by_name = await repository.search_repairs('حسین')
    assert len(by_name) == 1
    by_device = await repository.search_repairs('Samsung')
    assert len(by_device) == 1

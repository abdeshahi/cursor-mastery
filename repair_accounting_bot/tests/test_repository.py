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
async def test_allocate_technician_payment(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('رضا', '09120000000')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='iPhone 12',
        issue='تاچ',
        labor_amount=600_000,
        technician_pct=40,
        parts=[],
    )
    applied = await repository.allocate_technician_payment(tech_id, 100_000)
    assert applied == [(repair_id, 100_000)]
    repair = await repository.get_repair(repair_id)
    assert repair['totals'].technician_paid == 100_000
    assert repair['totals'].technician_debt == 140_000


@pytest.mark.asyncio
async def test_allocate_technician_payment_full(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('علی', '09121111111')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='Samsung',
        issue='باتری',
        labor_amount=500_000,
        technician_pct=40,
        parts=[],
    )
    applied = await repository.allocate_technician_payment(tech_id, 500_000)
    assert applied == [(repair_id, 200_000)]


@pytest.mark.asyncio
async def test_allocate_customer_payment(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('مریم', '09123333333')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='iPhone 13',
        issue='صفحه',
        labor_amount=800_000,
        technician_pct=40,
        parts=[{'part_name': 'LCD', 'cost': 1_500_000, 'sell_price': 2_000_000, 'supplier_id': None}],
    )
    applied = await repository.allocate_customer_payment(customer_id, 1_000_000)
    assert applied == [(repair_id, 1_000_000)]
    repair = await repository.get_repair(repair_id)
    assert repair['totals'].customer_paid == 1_000_000
    assert repair['totals'].customer_debt == 1_800_000


@pytest.mark.asyncio
async def test_allocate_customer_payment_full(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('سارا', '09124444444')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='Xiaomi',
        issue='شارژ',
        labor_amount=300_000,
        technician_pct=40,
        parts=[],
    )
    applied = await repository.allocate_customer_payment(customer_id, 500_000)
    assert applied == [(repair_id, 300_000)]
    repair = await repository.get_repair(repair_id)
    assert repair['totals'].customer_debt == 0


@pytest.mark.asyncio
async def test_update_repair_labor(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('کامیل', '09125555555')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='Nokia',
        issue='باتری',
        labor_amount=0,
        technician_pct=40,
        parts=[],
    )
    assert await repository.update_repair_labor(repair_id, 450_000)
    repair = await repository.get_repair(repair_id)
    assert repair['labor_amount'] == 450_000
    assert repair['totals'].technician_share == 180_000


@pytest.mark.asyncio
async def test_add_repair_part(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('نیما', '09126666666')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='Huawei',
        issue='LCD',
        labor_amount=200_000,
        technician_pct=40,
        parts=[],
    )
    assert await repository.add_repair_part(
        repair_id,
        {'part_name': 'LCD', 'cost': 800_000, 'sell_price': 1_100_000, 'supplier_id': None},
    )
    repair = await repository.get_repair(repair_id)
    assert len(repair['parts']) == 1
    assert repair['parts_cost'] == 800_000
    assert repair['parts_sell'] == 1_100_000
    assert repair['totals'].customer_total == 1_300_000


@pytest.mark.asyncio
async def test_update_repair_labor_closed(repo) -> None:
    repository, tech_id = repo
    customer_id = await repository.find_or_create_customer('بسته', '09127777777')
    repair_id = await repository.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='LG',
        issue='test',
        labor_amount=100_000,
        technician_pct=40,
        parts=[],
    )
    await repository.close_repair(repair_id)
    assert not await repository.update_repair_labor(repair_id, 200_000)


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

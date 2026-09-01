import pytest
import pytest_asyncio

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
    assert repair['totals'].customer_debt == 3_100_000
    assert repair['totals'].supplier_debt == 2_000_000

    await repository.add_customer_payment(repair_id, 1_000_000)
    await repository.add_supplier_payment(repair_id, 500_000)
    repair = await repository.get_repair(repair_id)
    assert repair['totals'].customer_debt == 2_100_000
    assert repair['totals'].supplier_debt == 1_500_000

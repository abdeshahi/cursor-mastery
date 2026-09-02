import pytest
import pytest_asyncio

from app.services.export_service import ExportService
from app.storage.db import Database
from app.storage.repository import RepairRepository


@pytest_asyncio.fixture
async def export_service(tmp_path):
    db = Database(str(tmp_path / 'test.db'))
    conn = await db.connect()
    repo = RepairRepository(conn)
    tech_id = await repo.add_technician('علی', 40)
    customer_id = await repo.find_or_create_customer('رضا', '09120000000')
    await repo.create_repair(
        customer_id=customer_id,
        technician_id=tech_id,
        device='iPhone 12',
        issue='تاچ',
        labor_amount=500_000,
        technician_pct=40,
        parts=[{'part_name': 'LCD', 'cost': 1_000_000, 'sell_price': 1_300_000, 'supplier_id': None}],
    )
    service = ExportService(repo, tmp_path / 'exports')
    yield service, repo
    await conn.close()


@pytest.mark.asyncio
async def test_export_accounting_excel(export_service) -> None:
    service, _repo = export_service
    path = await service.export_accounting_excel()
    assert path.exists()
    assert path.suffix == '.xlsx'
    assert path.stat().st_size > 500


@pytest.mark.asyncio
async def test_export_accounting_pdf(export_service) -> None:
    service, _repo = export_service
    path = await service.export_accounting_pdf()
    assert path.exists()
    assert path.suffix == '.pdf'
    assert path.read_bytes()[:4] == b'%PDF'


@pytest.mark.asyncio
async def test_export_invoice_files(export_service) -> None:
    service, _repo = export_service
    xlsx = await service.export_invoice_excel(1)
    pdf = await service.export_invoice_pdf(1)
    assert xlsx is not None and xlsx.exists()
    assert pdf is not None and pdf.exists()
    # Letterhead artwork makes invoice PDFs noticeably larger than a plain text PDF.
    assert pdf.stat().st_size > 20_000

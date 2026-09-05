from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.services.excel_export import build_accounting_workbook, build_invoice_workbook, save_workbook
from app.services.pdf_export import build_accounting_pdf, build_invoice_pdf
from app.storage.repository import RepairRepository
from app.storage.settings_repository import SettingsRepository
from app.ui.themes import Theme, get_theme


class ExportService:
    def __init__(
        self,
        repo: RepairRepository,
        export_dir: Path,
        settings_repo: SettingsRepository,
    ) -> None:
        self.repo = repo
        self.export_dir = export_dir
        self.settings_repo = settings_repo

    async def _theme(self) -> Theme:
        return await self.settings_repo.get_theme()

    def _timestamp(self) -> str:
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    async def _collect_accounting_data(self):
        dashboard = await self.repo.accounting_dashboard()
        customer_debts = await self.repo.customer_debts(limit=200)
        repairs = await self.repo.list_open_repairs_full(limit=200)
        return dashboard, customer_debts, repairs

    async def export_accounting_excel(self) -> Path:
        dashboard, customer_debts, repairs = await self._collect_accounting_data()
        wb = build_accounting_workbook(dashboard, repairs, customer_debts)
        path = self.export_dir / f'accounting_{self._timestamp()}.xlsx'
        return save_workbook(wb, path)

    async def export_accounting_pdf(self) -> Path:
        dashboard, customer_debts, repairs = await self._collect_accounting_data()
        path = self.export_dir / f'accounting_{self._timestamp()}.pdf'
        return build_accounting_pdf(dashboard, repairs, customer_debts, path, theme=await self._theme())

    async def export_invoice_excel(self, repair_id: int) -> Path | None:
        repair = await self.repo.get_repair(repair_id)
        if not repair:
            return None
        wb = build_invoice_workbook(repair)
        path = self.export_dir / f'invoice_{repair_id}_{self._timestamp()}.xlsx'
        return save_workbook(wb, path)

    async def export_invoice_pdf(self, repair_id: int) -> Path | None:
        repair = await self.repo.get_repair(repair_id)
        if not repair:
            return None
        path = self.export_dir / f'invoice_{repair_id}_{self._timestamp()}.pdf'
        return build_invoice_pdf(repair, path, theme=await self._theme())

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.export_service import ExportService
from app.storage.repository import RepairRepository
from app.storage.settings_repository import SettingsRepository
from app.storage.staff_repository import StaffRepository


class RepositoryMiddleware(BaseMiddleware):
    def __init__(
        self,
        repo: RepairRepository,
        export_service: ExportService,
        staff_repo: StaffRepository,
        settings_repo: SettingsRepository,
    ) -> None:
        self.repo = repo
        self.export_service = export_service
        self.staff_repo = staff_repo
        self.settings_repo = settings_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data['repo'] = self.repo
        data['export_service'] = self.export_service
        data['staff_repo'] = self.staff_repo
        data['settings_repo'] = self.settings_repo
        data['theme'] = await self.settings_repo.get_theme()
        return await handler(event, data)

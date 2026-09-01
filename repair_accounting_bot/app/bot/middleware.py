from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.export_service import ExportService
from app.storage.repository import RepairRepository


class RepositoryMiddleware(BaseMiddleware):
    def __init__(self, repo: RepairRepository, export_service: ExportService) -> None:
        self.repo = repo
        self.export_service = export_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data['repo'] = self.repo
        data['export_service'] = self.export_service
        return await handler(event, data)

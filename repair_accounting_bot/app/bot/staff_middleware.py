from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.storage.staff_repository import StaffRepository


def _user_id_from_event(event: TelegramObject) -> int | None:
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    if isinstance(event, Update):
        if event.message and event.message.from_user:
            return event.message.from_user.id
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user.id
    return None


class StaffGuardMiddleware(BaseMiddleware):
    def __init__(self, staff_repo: StaffRepository) -> None:
        self.staff_repo = staff_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _user_id_from_event(event)
        if user_id is None:
            return await handler(event, data)

        if not await self.staff_repo.is_active_staff(user_id):
            deny = '⛔️ فقط پرسنل مجاز می‌توانند از این بات استفاده کنند.'
            if isinstance(event, Message):
                await event.answer(deny)
            elif isinstance(event, CallbackQuery):
                await event.answer(deny, show_alert=True)
            elif isinstance(event, Update):
                if event.message:
                    await event.message.answer(deny)
                elif event.callback_query:
                    await event.callback_query.answer(deny, show_alert=True)
            return None

        data['is_admin'] = await self.staff_repo.is_admin(user_id)
        return await handler(event, data)

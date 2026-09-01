from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.bot.invite_utils import extract_invite_token
from app.staff.roles import role_permissions
from app.storage.staff_repository import StaffRepository

PUBLIC_COMMANDS = {'/myid'}


def _message_text(event: TelegramObject) -> str | None:
    if isinstance(event, Message) and event.text:
        return event.text.strip()
    if isinstance(event, Update) and event.message and event.message.text:
        return event.message.text.strip()
    return None


def _is_public_command(event: TelegramObject) -> bool:
    text = _message_text(event)
    if not text:
        return False
    command = text.split()[0].lower().split('@')[0]
    return command in PUBLIC_COMMANDS


def _deny_text(user_id: int) -> str:
    return (
        '⛔️ فقط پرسنل مجاز می‌توانند از این بات استفاده کنند.\n\n'
        f'🆔 آیدی تلگرام شما: `{user_id}`\n'
        'از مدیر بخواهید لینک دعوت پرسنل برایتان بفرستد، یا آیدی را به مدیر بدهید.'
    )


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

        if _is_public_command(event):
            if isinstance(event, Message):
                await event.answer(
                    f'🆔 آیدی تلگرام شما:\n`{user_id}`\n\n'
                    'از مدیر بخواهید لینک دعوت پرسنل برایتان بفرستد.',
                    parse_mode='Markdown',
                )
            elif isinstance(event, Update) and event.message:
                await event.message.answer(
                    f'🆔 آیدی تلگرام شما:\n`{user_id}`\n\n'
                    'از مدیر بخواهید لینک دعوت پرسنل برایتان بفرستد.',
                    parse_mode='Markdown',
                )
            return None

        if isinstance(event, Message) and event.text and event.from_user:
            invite_token = extract_invite_token(event.text)
            if invite_token:
                was_staff = await self.staff_repo.is_active_staff(user_id)
                display_name = (
                    event.from_user.full_name
                    or event.from_user.first_name
                    or f'کاربر {user_id}'
                )
                invite_error = await self.staff_repo.try_redeem_invite(
                    invite_token,
                    user_id,
                    display_name,
                )
                if invite_error:
                    await event.answer(invite_error)
                    return None
                if not was_staff and await self.staff_repo.is_active_staff(user_id):
                    data['invite_joined'] = True

        if not await self.staff_repo.is_active_staff(user_id):
            deny = _deny_text(user_id)
            if isinstance(event, Message):
                await event.answer(deny, parse_mode='Markdown')
            elif isinstance(event, CallbackQuery):
                await event.answer('فقط پرسنل مجاز.', show_alert=True)
            elif isinstance(event, Update):
                if event.message:
                    await event.message.answer(deny, parse_mode='Markdown')
                elif event.callback_query:
                    await event.callback_query.answer('فقط پرسنل مجاز.', show_alert=True)
            return None

        role = await self.staff_repo.get_role(user_id) or 'full'
        perms = role_permissions(role)
        data['staff_role'] = role
        data['is_admin'] = perms['manage']
        data['can_manage'] = perms['manage']
        data['can_reception'] = perms['reception']
        data['can_accounting'] = perms['accounting']
        return await handler(event, data)

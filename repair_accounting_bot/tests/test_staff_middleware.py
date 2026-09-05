from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram.types import Chat, Message, Update, User

from app.bot.staff_middleware import StaffGuardMiddleware
from app.config import settings
from app.staff.roles import ROLE_RECEPTION
from app.storage.db import Database
from app.storage.staff_repository import StaffRepository


@pytest_asyncio.fixture
async def staff_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('ALLOWED_USER_IDS', '111')
    monkeypatch.setenv('ADMIN_USER_IDS', '111')
    settings.ALLOWED_USER_IDS = '111'
    settings.ADMIN_USER_IDS = '111'
    db = Database(str(tmp_path / 'middleware.db'))
    conn = await db.connect()
    repo = StaffRepository(conn)
    await repo.seed_from_env()
    yield repo
    await conn.close()


def _make_update(text: str, user_id: int = 5543163454) -> Update:
    user = User(id=user_id, is_bot=False, first_name='نهال')
    chat = Chat(id=user_id, type='private')
    message = Message(
        message_id=1,
        date=0,
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=1, message=message)


@pytest.mark.asyncio
async def test_invite_redeem_via_update_object(staff_repo: StaffRepository) -> None:
    token = await staff_repo.create_invite(111, ROLE_RECEPTION, max_uses=1)
    middleware = StaffGuardMiddleware(staff_repo)
    handler = AsyncMock(return_value='ok')
    update = _make_update(f'/start {token}', user_id=5543163454)
    data: dict = {}

    result = await middleware(handler, update, data)

    assert result == 'ok'
    assert data.get('invite_joined') is True
    assert await staff_repo.is_active_staff(5543163454)
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_plain_start_denied_for_non_staff(staff_repo: StaffRepository, monkeypatch) -> None:
    deny = AsyncMock()
    monkeypatch.setattr('app.bot.staff_middleware._answer_deny', deny)
    middleware = StaffGuardMiddleware(staff_repo)
    handler = AsyncMock()
    update = _make_update('/start', user_id=999888777)
    data: dict = {}

    result = await middleware(handler, update, data)

    assert result is None
    handler.assert_not_awaited()
    deny.assert_awaited_once()
    assert not await staff_repo.is_active_staff(999888777)


@pytest.mark.asyncio
async def test_used_invite_shows_error(staff_repo: StaffRepository, monkeypatch) -> None:
    token = await staff_repo.create_invite(111, ROLE_RECEPTION, max_uses=1)
    await staff_repo.try_redeem_invite(token, 100, 'اول')
    monkeypatch.setattr(Message, 'answer', AsyncMock(return_value=None))
    middleware = StaffGuardMiddleware(staff_repo)
    handler = AsyncMock()
    update = _make_update(f'/start {token}', user_id=200)
    data: dict = {}

    result = await middleware(handler, update, data)

    assert result is None
    handler.assert_not_awaited()
    assert not await staff_repo.is_active_staff(200)

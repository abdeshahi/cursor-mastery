import pytest
import pytest_asyncio

from app.config import settings
from app.staff.roles import ROLE_ACCOUNTANT, ROLE_RECEPTION
from app.storage.db import Database
from app.storage.staff_repository import StaffRepository


@pytest_asyncio.fixture
async def staff_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('ALLOWED_USER_IDS', '111,222')
    monkeypatch.setenv('ADMIN_USER_IDS', '111')
    settings.ALLOWED_USER_IDS = '111,222'
    settings.ADMIN_USER_IDS = '111'
    db = Database(str(tmp_path / 'staff.db'))
    conn = await db.connect()
    repo = StaffRepository(conn)
    yield repo
    await conn.close()


@pytest.mark.asyncio
async def test_seed_from_env(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    assert await staff_repo.is_active_staff(111)
    assert await staff_repo.is_active_staff(222)
    assert await staff_repo.is_admin(111)
    assert not await staff_repo.is_admin(222)
    assert not await staff_repo.is_active_staff(999)


@pytest.mark.asyncio
async def test_add_and_remove_staff(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    await staff_repo.add_staff(333, 'رضا')
    assert await staff_repo.is_active_staff(333)
    assert await staff_repo.remove_staff(333)
    assert not await staff_repo.is_active_staff(333)


@pytest.mark.asyncio
async def test_re_add_preserves_admin(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    await staff_repo.add_staff(111, 'مدیر جدید')
    assert await staff_repo.is_admin(111)


@pytest.mark.asyncio
async def test_create_and_redeem_invite(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    token = await staff_repo.create_invite(111, ROLE_RECEPTION, max_uses=1)
    assert token.startswith('inv_')
    err = await staff_repo.try_redeem_invite(token, 999, 'نهال')
    assert err is None
    assert await staff_repo.is_active_staff(999)
    assert await staff_repo.get_role(999) == ROLE_RECEPTION
    err2 = await staff_repo.try_redeem_invite(token, 888, 'دیگری')
    assert err2 is not None


@pytest.mark.asyncio
async def test_set_name(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    assert await staff_repo.set_name(111, 'مدیر اصلی')
    row = await staff_repo.get_staff(111)
    assert row is not None
    assert row['name'] == 'مدیر اصلی'


@pytest.mark.asyncio
async def test_set_role(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    assert await staff_repo.set_role(222, ROLE_ACCOUNTANT)
    assert await staff_repo.get_role(222) == ROLE_ACCOUNTANT
    assert not await staff_repo.is_admin(222)


@pytest.mark.asyncio
async def test_list_staff(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    rows = await staff_repo.list_staff()
    ids = {row['telegram_id'] for row in rows}
    assert ids == {111, 222}

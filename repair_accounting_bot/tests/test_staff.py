import pytest
import pytest_asyncio

from app.config import settings
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
async def test_list_staff(staff_repo: StaffRepository) -> None:
    await staff_repo.seed_from_env()
    rows = await staff_repo.list_staff()
    ids = {row['telegram_id'] for row in rows}
    assert ids == {111, 222}

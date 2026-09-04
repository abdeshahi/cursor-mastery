"""Tests for async database utilities."""

import pytest

from app.core.config import get_settings
from app.database.db import check_database_connection, create_engine, dispose_engine


@pytest.mark.asyncio
async def test_create_engine_is_singleton(test_settings) -> None:
    await dispose_engine()
    engine_a = create_engine(test_settings)
    engine_b = create_engine(test_settings)
    assert engine_a is engine_b
    await dispose_engine()


@pytest.mark.asyncio
async def test_check_database_connection_returns_tuple(test_settings) -> None:
    await dispose_engine()
    create_engine(test_settings)
    ok, error = await check_database_connection()
    assert isinstance(ok, bool)
    assert error is None or isinstance(error, str)
    await dispose_engine()

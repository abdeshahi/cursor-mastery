"""Tests for FRED provider parsing."""

from decimal import Decimal

import httpx
import pytest

from app.providers.market.fred import FREDProvider
from tests.helpers.providers import load_fixture, mock_transport


@pytest.mark.asyncio
async def test_fred_parses_brent_usd() -> None:
    payload = load_fixture("fred_brent.json")
    transport = mock_transport({"series/observations": payload})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = FREDProvider(api_key="a" * 32, client=client)
        result = await provider.fetch_price("BRENT_USD")

    assert result.success is True
    assert result.quotes[0].price == Decimal("68.45")
    assert result.quotes[0].symbol == "BRENT_USD"


@pytest.mark.asyncio
async def test_fred_blocked_without_api_key() -> None:
    provider = FREDProvider(api_key=None)
    result = await provider.fetch_price("BRENT_USD")
    assert result.success is False
    assert "FRED_API_KEY" in (result.error or "")

"""Tests for Nobitex provider parsing."""

from decimal import Decimal

import httpx
import pytest

from app.core.constants import MarketSymbol
from app.providers.market.nobitex import NobitexProvider
from tests.helpers.providers import load_fixture, mock_transport


@pytest.mark.asyncio
async def test_nobitex_parses_and_converts_toman_to_irr() -> None:
    payload = load_fixture("nobitex_orderbook.json")
    transport = mock_transport({"orderbook/USDTIRT": payload})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NobitexProvider(client=client)
        result = await provider.fetch_price(MarketSymbol.USDT_IRR.value)

    assert result.success is True
    quote = result.quotes[0]
    assert quote.price == Decimal("2197500")
    assert quote.bid == Decimal("2195000")
    assert quote.ask == Decimal("2200000")


@pytest.mark.asyncio
async def test_nobitex_malformed_status() -> None:
    transport = mock_transport({"orderbook/USDTIRT": {"status": "failed"}})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NobitexProvider(client=client)
        result = await provider.fetch_price(MarketSymbol.USDT_IRR.value)

    assert result.success is False

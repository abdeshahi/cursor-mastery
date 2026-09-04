"""Tests for Wallex provider parsing."""

from decimal import Decimal

import httpx
import pytest

from app.core.constants import MarketSymbol
from app.providers.market.wallex import WallexProvider
from tests.helpers.providers import load_fixture, mock_transport


@pytest.mark.asyncio
async def test_wallex_parses_and_converts_toman_to_irr() -> None:
    payload = load_fixture("wallex_depth.json")
    transport = mock_transport({"depth": payload})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = WallexProvider(client=client)
        result = await provider.fetch_price(MarketSymbol.USDT_IRR.value)

    assert result.success is True
    quote = result.quotes[0]
    assert quote.price == Decimal("2199480")
    assert quote.bid == Decimal("2196670")
    assert quote.ask == Decimal("2202290")


@pytest.mark.asyncio
async def test_wallex_empty_depth_fails() -> None:
    transport = mock_transport({"depth": {"result": {"ask": [], "bid": []}}})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = WallexProvider(client=client)
        result = await provider.fetch_price(MarketSymbol.USDT_IRR.value)

    assert result.success is False

"""Tests for Alpha Vantage provider parsing."""

from decimal import Decimal

import httpx
import pytest

from app.core.constants import MarketSymbol
from app.providers.market.alphavantage import AlphaVantageProvider
from tests.helpers.providers import load_fixture, mock_transport


@pytest.mark.asyncio
async def test_alphavantage_parses_gold_ounce_usd() -> None:
    payload = load_fixture("alphavantage_xauusd.json")
    transport = mock_transport({"query": payload})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = AlphaVantageProvider(api_key="demo-key", client=client)
        result = await provider.fetch_price(MarketSymbol.GOLD_OUNCE_USD.value)

    assert result.success is True
    quote = result.quotes[0]
    assert quote.symbol == MarketSymbol.GOLD_OUNCE_USD.value
    assert quote.price == Decimal("2650.12000000")
    assert quote.bid == Decimal("2649.50000000")
    assert quote.ask == Decimal("2650.80000000")


@pytest.mark.asyncio
async def test_alphavantage_blocked_without_api_key() -> None:
    provider = AlphaVantageProvider(api_key=None)
    result = await provider.fetch_price(MarketSymbol.GOLD_OUNCE_USD.value)
    assert result.success is False

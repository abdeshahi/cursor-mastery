"""Tests for TGJU provider parsing."""

from decimal import Decimal

import httpx
import pytest

from app.core.constants import MarketSymbol
from app.providers.market.tgju import TGJUProvider
from tests.helpers.providers import load_fixture, mock_transport


@pytest.mark.asyncio
async def test_tgju_parses_usd_price() -> None:
    payload = load_fixture("tgju_usd.json")
    transport = mock_transport({"price_dollar_rl": payload})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = TGJUProvider(client=client, stale_after_seconds=999999)
        result = await provider.fetch_price(MarketSymbol.USD_IRR.value)

    assert result.success is True
    assert len(result.quotes) == 1
    quote = result.quotes[0]
    assert quote.symbol == MarketSymbol.USD_IRR.value
    assert quote.price == Decimal("2214200")
    assert quote.bid is None
    assert quote.ask is None


@pytest.mark.asyncio
async def test_tgju_malformed_response_fails() -> None:
    transport = mock_transport({"price_dollar_rl": {"data": []}})
    async with httpx.AsyncClient(transport=transport) as client:
        provider = TGJUProvider(client=client)
        result = await provider.fetch_price(MarketSymbol.USD_IRR.value)

    assert result.success is False
    assert result.failures

"""Nobitex USDT market data provider.

Public orderbook endpoint:
  GET https://api.nobitex.ir/v3/orderbook/USDTIRT

Quote unit: Nobitex `IRT` destination currency is TOMAN (not Rial).
All stored values are normalized to IRR using the explicit 1 TOMAN = 10 IRR rule.
"""

from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import httpx

from app.core.constants import MarketSymbol
from app.core.logging import get_logger
from app.providers.market.base import MarketDataProvider
from app.providers.market.http_client import ResilientHttpClient
from app.providers.market.units import parse_decimal, toman_to_irr
from app.schemas.provider import NormalizedQuote, ProviderFailure, ProviderFetchResult, QuoteUnit

logger = get_logger(__name__)

TEHRAN = ZoneInfo("Asia/Tehran")


class NobitexProvider(MarketDataProvider):
    """Fetch USDT/IRT orderbook from Nobitex and normalize to USDT_IRR in Rial."""

    source_name = "nobitex"

    def __init__(
        self,
        *,
        orderbook_url: str = "https://api.nobitex.ir/v3/orderbook/USDTIRT",
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._orderbook_url = orderbook_url
        self._http = http_client or ResilientHttpClient()
        self._client = client

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset({MarketSymbol.USDT_IRR.value})

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        requested = set(symbols or self.supported_symbols)
        symbol = MarketSymbol.USDT_IRR.value
        if requested - self.supported_symbols:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error="Nobitex only supports USDT_IRR",
            )

        started = perf_counter()
        try:
            payload = await self._http.get_json(self._orderbook_url, client=self._client)
            quote = self._parse_orderbook(payload, symbol)
            latency_ms = int((perf_counter() - started) * 1000)
            return ProviderFetchResult(
                source=self.source_name,
                success=True,
                quotes=[quote],
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            logger.warning("Nobitex fetch failed", extra={"error": str(exc)})
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                failures=[ProviderFailure(source=self.source_name, symbol=symbol, error=str(exc), latency_ms=latency_ms)],
                latency_ms=latency_ms,
                error=str(exc),
            )

    def _parse_orderbook(self, payload: dict, symbol: str) -> NormalizedQuote:
        if payload.get("status") != "ok":
            raise ValueError("Nobitex response status is not ok")

        asks = payload.get("asks") or []
        bids = payload.get("bids") or []
        if not asks and not bids:
            raise ValueError("Nobitex orderbook is empty")

        best_ask_toman = parse_decimal(str(asks[0][0])) if asks else None
        best_bid_toman = parse_decimal(str(bids[0][0])) if bids else None

        if best_ask_toman is not None and best_bid_toman is not None:
            price_toman = (best_bid_toman + best_ask_toman) / 2
        elif best_ask_toman is not None:
            price_toman = best_ask_toman
        elif best_bid_toman is not None:
            price_toman = best_bid_toman
        else:
            raise ValueError("Nobitex orderbook has no usable prices")

        last_update = payload.get("lastUpdate")
        if isinstance(last_update, (int, float)) and last_update > 0:
            market_timestamp = datetime.fromtimestamp(last_update, tz=TEHRAN)
        else:
            market_timestamp = datetime.now(tz=TEHRAN)

        received_at = datetime.now(tz=TEHRAN)
        return NormalizedQuote(
            symbol=symbol,
            price=toman_to_irr(price_toman),
            bid=toman_to_irr(best_bid_toman) if best_bid_toman is not None else None,
            ask=toman_to_irr(best_ask_toman) if best_ask_toman is not None else None,
            source=self.source_name,
            market_timestamp=market_timestamp,
            received_at=received_at,
            quote_unit=QuoteUnit.IRR,
        )

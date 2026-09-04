"""Wallex USDT market data provider.

Public depth endpoint:
  GET https://api.wallex.ir/v1/depth?symbol=USDTTMN

Quote unit: Wallex `TMN` is TOMAN.
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


class WallexProvider(MarketDataProvider):
    """Fetch USDT/TMN depth from Wallex and normalize to USDT_IRR in Rial."""

    source_name = "wallex"

    def __init__(
        self,
        *,
        depth_url: str = "https://api.wallex.ir/v1/depth",
        symbol: str = "USDTTMN",
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._depth_url = depth_url
        self._symbol = symbol
        self._http = http_client or ResilientHttpClient()
        self._client = client

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset({MarketSymbol.USDT_IRR.value})

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        if symbols and set(symbols) - self.supported_symbols:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error="Wallex only supports USDT_IRR",
            )

        internal_symbol = MarketSymbol.USDT_IRR.value
        started = perf_counter()
        try:
            payload = await self._http.get_json(
                self._depth_url,
                params={"symbol": self._symbol},
                client=self._client,
            )
            quote = self._parse_depth(payload, internal_symbol)
            latency_ms = int((perf_counter() - started) * 1000)
            return ProviderFetchResult(
                source=self.source_name,
                success=True,
                quotes=[quote],
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            logger.warning("Wallex fetch failed", extra={"error": str(exc)})
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                failures=[
                    ProviderFailure(
                        source=self.source_name,
                        symbol=internal_symbol,
                        error=str(exc),
                        latency_ms=latency_ms,
                    )
                ],
                latency_ms=latency_ms,
                error=str(exc),
            )

    def _parse_depth(self, payload: dict, symbol: str) -> NormalizedQuote:
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("Wallex response missing result object")

        asks = result.get("ask") or []
        bids = result.get("bid") or []
        if not asks and not bids:
            raise ValueError("Wallex depth is empty")

        best_ask_toman = parse_decimal(str(asks[0]["price"])) if asks else None
        best_bid_toman = parse_decimal(str(bids[0]["price"])) if bids else None

        if best_ask_toman is not None and best_bid_toman is not None:
            price_toman = (best_bid_toman + best_ask_toman) / 2
        elif best_ask_toman is not None:
            price_toman = best_ask_toman
        elif best_bid_toman is not None:
            price_toman = best_bid_toman
        else:
            raise ValueError("Wallex depth has no usable prices")

        received_at = datetime.now(tz=TEHRAN)
        return NormalizedQuote(
            symbol=symbol,
            price=toman_to_irr(price_toman),
            bid=toman_to_irr(best_bid_toman) if best_bid_toman is not None else None,
            ask=toman_to_irr(best_ask_toman) if best_ask_toman is not None else None,
            source=self.source_name,
            market_timestamp=received_at,
            received_at=received_at,
            quote_unit=QuoteUnit.IRR,
        )

"""Alpha Vantage market data provider.

Gold endpoint:
  function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD

Returns USD per troy ounce (XAU/USD).
"""

from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import httpx

from app.core.constants import MarketSymbol
from app.core.logging import get_logger
from app.providers.market.base import MarketDataProvider
from app.providers.market.http_client import ResilientHttpClient
from app.providers.market.units import parse_decimal
from app.schemas.provider import NormalizedQuote, ProviderFailure, ProviderFetchResult, QuoteUnit

logger = get_logger(__name__)

UTC = ZoneInfo("UTC")


class AlphaVantageProvider(MarketDataProvider):
    """Fetch global market quotes from Alpha Vantage."""

    source_name = "alphavantage"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://www.alphavantage.co/query",
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._http = http_client or ResilientHttpClient()
        self._client = client

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset({MarketSymbol.GOLD_OUNCE_USD.value})

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        if not self._api_key:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error="ALPHAVANTAGE_API_KEY is not configured",
            )

        requested = set(symbols or self.supported_symbols)
        if requested - self.supported_symbols:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error="Alpha Vantage Phase 3 supports GOLD_OUNCE_USD only",
            )

        symbol = MarketSymbol.GOLD_OUNCE_USD.value
        started = perf_counter()
        try:
            payload = await self._http.get_json(
                self._base_url,
                params={
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": "XAU",
                    "to_currency": "USD",
                    "apikey": self._api_key,
                },
                client=self._client,
            )
            quote = self._parse_xau_usd(payload, symbol)
            latency_ms = int((perf_counter() - started) * 1000)
            return ProviderFetchResult(
                source=self.source_name,
                success=True,
                quotes=[quote],
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            logger.warning("Alpha Vantage fetch failed", extra={"error": str(exc)})
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                failures=[
                    ProviderFailure(
                        source=self.source_name,
                        symbol=symbol,
                        error=str(exc),
                        latency_ms=latency_ms,
                    )
                ],
                latency_ms=latency_ms,
                error=str(exc),
            )

    def _parse_xau_usd(self, payload: dict, symbol: str) -> NormalizedQuote:
        if "Note" in payload or "Information" in payload:
            raise ValueError("Alpha Vantage rate limit or informational response")

        rate_block = payload.get("Realtime Currency Exchange Rate")
        if not isinstance(rate_block, dict):
            raise ValueError("Alpha Vantage response missing exchange rate block")

        price = parse_decimal(str(rate_block.get("5. Exchange Rate", "")))
        if price <= 0:
            raise ValueError("Alpha Vantage price must be positive")

        raw_time = rate_block.get("6. Last Refreshed")
        if not raw_time:
            raise ValueError("Alpha Vantage missing last refreshed timestamp")

        market_timestamp = datetime.strptime(str(raw_time), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        received_at = datetime.now(tz=UTC)

        bid_raw = rate_block.get("8. Bid Price")
        ask_raw = rate_block.get("9. Ask Price")
        bid = parse_decimal(str(bid_raw)) if bid_raw not in (None, "") else None
        ask = parse_decimal(str(ask_raw)) if ask_raw not in (None, "") else None

        return NormalizedQuote(
            symbol=symbol,
            price=price,
            bid=bid if bid and bid > 0 else None,
            ask=ask if ask and ask > 0 else None,
            source=self.source_name,
            market_timestamp=market_timestamp,
            received_at=received_at,
            quote_unit=QuoteUnit.USD,
        )

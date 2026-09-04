"""FRED macro market data provider.

Series mapping:
- BRENT_USD  <- DCOILBRENTEU (Brent Spot Price, USD per barrel)
- USD_BROAD_INDEX <- DTWEXBGS (Trade Weighted U.S. Dollar Index: Broad)

Important: DTWEXBGS is NOT the ICE DXY index. It is stored as USD_BROAD_INDEX.
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

FRED_SERIES_MAP: dict[str, str] = {
    MarketSymbol.BRENT_USD.value: "DCOILBRENTEU",
    "USD_BROAD_INDEX": "DTWEXBGS",
}


class FREDProvider(MarketDataProvider):
    """Fetch macro series from the FRED API."""

    source_name = "fred"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://api.stlouisfed.org/fred/series/observations",
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._http = http_client or ResilientHttpClient()
        self._client = client

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset(FRED_SERIES_MAP.keys())

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        if not self._api_key:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error="FRED_API_KEY is not configured",
            )

        requested = set(symbols or self.supported_symbols)
        unknown = requested - self.supported_symbols
        if unknown:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error=f"unsupported symbols for FRED: {sorted(unknown)}",
            )

        started = perf_counter()
        quotes: list[NormalizedQuote] = []
        failures: list[ProviderFailure] = []

        for symbol in requested:
            series_id = FRED_SERIES_MAP[symbol]
            try:
                quotes.append(await self._fetch_series(symbol, series_id))
            except Exception as exc:
                logger.warning("FRED fetch failed", extra={"symbol": symbol, "error": str(exc)})
                failures.append(ProviderFailure(source=self.source_name, symbol=symbol, error=str(exc)))

        latency_ms = int((perf_counter() - started) * 1000)
        return ProviderFetchResult(
            source=self.source_name,
            success=bool(quotes),
            quotes=quotes,
            failures=failures,
            latency_ms=latency_ms,
            error=failures[0].error if failures and not quotes else None,
        )

    async def _fetch_series(self, symbol: str, series_id: str) -> NormalizedQuote:
        payload = await self._http.get_json(
            self._base_url,
            params={
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 5,
            },
            client=self._client,
        )
        return self._parse_observations(payload, symbol)

    def _parse_observations(self, payload: dict, symbol: str) -> NormalizedQuote:
        observations = payload.get("observations")
        if not isinstance(observations, list):
            raise ValueError("FRED response missing observations")

        for observation in observations:
            raw_value = observation.get("value")
            raw_date = observation.get("date")
            if raw_value in (None, ".", ""):
                continue
            price = parse_decimal(str(raw_value))
            if price <= 0:
                continue
            market_timestamp = datetime.strptime(str(raw_date), "%Y-%m-%d").replace(tzinfo=UTC)
            received_at = datetime.now(tz=UTC)
            quote_unit = QuoteUnit.INDEX if symbol == "USD_BROAD_INDEX" else QuoteUnit.USD
            return NormalizedQuote(
                symbol=symbol,
                price=price,
                bid=None,
                ask=None,
                source=self.source_name,
                market_timestamp=market_timestamp,
                received_at=received_at,
                quote_unit=quote_unit,
            )

        raise ValueError("FRED returned no valid observations")

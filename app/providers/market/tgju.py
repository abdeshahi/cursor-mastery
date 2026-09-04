"""TGJU market data provider.

Uses TGJU public summary-table JSON endpoints. This adapter is intentionally isolated;
TGJU response structure may change without notice.

Endpoint pattern (fragile):
  https://api.tgju.org/v1/market/indicator/summary-table-data/{indicator_key}

Indicator keys are TGJU-specific and mapped internally to internal symbols.
Prices are returned in Iranian Rial (IRR).
GOLD_18K_IRR uses geram18: IRR per gram of 18-karat gold.
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

TEHRAN = ZoneInfo("Asia/Tehran")

# TGJU indicator slug -> internal symbol
TGJU_SYMBOL_MAP: dict[str, str] = {
    "price_dollar_rl": MarketSymbol.USD_IRR.value,
    "price_aed": MarketSymbol.AED_IRR.value,
    "geram18": MarketSymbol.GOLD_18K_IRR.value,
}


class TGJUProvider(MarketDataProvider):
    """Fetch USD/AED/Gold prices from TGJU public JSON endpoints."""

    source_name = "tgju"

    def __init__(
        self,
        *,
        base_url: str = "https://api.tgju.org/v1/market/indicator/summary-table-data",
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
        stale_after_seconds: int = 86_400,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http = http_client or ResilientHttpClient()
        self._client = client
        self._stale_after_seconds = stale_after_seconds

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset(TGJU_SYMBOL_MAP.values())

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        requested = set(symbols or self.supported_symbols)
        unknown = requested - self.supported_symbols
        if unknown:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                error=f"unsupported symbols for TGJU: {sorted(unknown)}",
                failures=[
                    ProviderFailure(source=self.source_name, symbol=symbol, error="unsupported symbol")
                    for symbol in sorted(unknown)
                ],
            )

        started = perf_counter()
        quotes: list[NormalizedQuote] = []
        failures: list[ProviderFailure] = []

        for indicator, symbol in TGJU_SYMBOL_MAP.items():
            if symbol not in requested:
                continue
            try:
                quotes.append(await self._fetch_indicator(indicator, symbol))
            except Exception as exc:
                logger.warning("TGJU fetch failed", extra={"symbol": symbol, "error": str(exc)})
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

    async def _fetch_indicator(self, indicator: str, symbol: str) -> NormalizedQuote:
        url = f"{self._base_url}/{indicator}"
        payload = await self._http.get_json(url, client=self._client)
        return self._parse_summary_table(payload, symbol)

    def _parse_summary_table(self, payload: dict, symbol: str) -> NormalizedQuote:
        rows = payload.get("data")
        if not isinstance(rows, list) or not rows:
            raise ValueError("TGJU response missing data rows")

        row = rows[0]
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError("TGJU row has unexpected shape")

        price = parse_decimal(str(row[0]))
        if price <= 0:
            raise ValueError("TGJU price must be positive")

        market_timestamp = self._parse_market_timestamp(str(row[6]))
        received_at = datetime.now(tz=TEHRAN)
        age_seconds = (received_at - market_timestamp).total_seconds()
        is_stale = age_seconds > self._stale_after_seconds

        return NormalizedQuote(
            symbol=symbol,
            price=price,
            bid=None,
            ask=None,
            source=self.source_name,
            market_timestamp=market_timestamp,
            received_at=received_at,
            quote_unit=QuoteUnit.IRR,
            is_stale=is_stale,
        )

    @staticmethod
    def _parse_market_timestamp(raw_date: str) -> datetime:
        # TGJU date format: YYYY/MM/DD in local Tehran calendar context
        parts = raw_date.strip().split("/")
        if len(parts) != 3:
            raise ValueError(f"invalid TGJU date: {raw_date}")
        year, month, day = (int(part) for part in parts)
        return datetime(year, month, day, 12, 0, tzinfo=TEHRAN)

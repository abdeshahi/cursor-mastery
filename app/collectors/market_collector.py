"""Asynchronous market data collectors."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import BaseCollector, CollectorRunResult
from app.core.config import Settings, get_settings
from app.core.constants import MarketSourceStatus
from app.core.logging import get_logger
from app.database.repositories.market_repository import MarketRepository
from app.providers.market.base import MarketDataProvider
from app.providers.market.validation import is_quote_stale, quote_to_market_price_create, utc_now
from app.schemas.market import MarketSourceHealthCreate
from app.schemas.provider import NormalizedQuote, ProviderFetchResult

logger = get_logger(__name__)


class MarketCollector(BaseCollector):
    """Fetch prices from providers and persist via repository."""

    def __init__(
        self,
        providers: list[MarketDataProvider],
        repository: MarketRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._providers = providers
        self._repository = repository or MarketRepository()
        self._settings = settings or get_settings()

    async def collect(self, session: AsyncSession) -> list[CollectorRunResult]:
        results: list[CollectorRunResult] = []
        for provider in self._providers:
            summary = CollectorRunResult(provider=provider.source_name)
            try:
                fetch_result = await provider.fetch_prices()
                await self._handle_fetch_result(session, fetch_result, summary)
            except Exception as exc:
                summary.failure_count += 1
                summary.errors.append(str(exc))
                logger.exception(
                    "Unhandled provider collector failure",
                    extra={"provider": provider.source_name, "error": str(exc)},
                )
            results.append(summary)
        return results

    async def _handle_fetch_result(
        self,
        session: AsyncSession,
        fetch_result: ProviderFetchResult,
        summary: CollectorRunResult,
    ) -> None:
        max_age = timedelta(seconds=self._settings.market_stale_after_seconds)

        for quote in fetch_result.quotes:
            try:
                await self._persist_quote(session, quote, fetch_result.latency_ms, max_age)
                summary.saved_count += 1
            except Exception as exc:
                summary.failure_count += 1
                summary.errors.append(f"{quote.symbol}: {exc}")
                await self._record_failure(
                    session,
                    source=fetch_result.source,
                    symbol=quote.symbol,
                    error=str(exc),
                    latency_ms=fetch_result.latency_ms,
                )

        for failure in fetch_result.failures:
            summary.failure_count += 1
            summary.errors.append(failure.error)
            await self._record_failure(
                session,
                source=failure.source,
                symbol=failure.symbol or "unknown",
                error=failure.error,
                latency_ms=failure.latency_ms or fetch_result.latency_ms,
            )

        if fetch_result.error and not fetch_result.quotes and not fetch_result.failures:
            summary.failure_count += 1
            summary.errors.append(fetch_result.error)
            await self._record_failure(
                session,
                source=fetch_result.source,
                symbol="unknown",
                error=fetch_result.error,
                latency_ms=fetch_result.latency_ms,
            )

    async def _persist_quote(
        self,
        session: AsyncSession,
        quote: NormalizedQuote,
        latency_ms: int,
        max_age: timedelta,
    ) -> None:
        if quote.symbol != quote.symbol.strip():
            raise ValueError("symbol must be valid")
        if quote.source != quote.source.strip():
            raise ValueError("source must be known")

        stale = is_quote_stale(quote, max_age=max_age)
        payload = quote_to_market_price_create(quote)
        await self._repository.save_price(session, payload)

        status = MarketSourceStatus.DEGRADED if stale else MarketSourceStatus.HEALTHY
        await self._record_success(
            session,
            source=quote.source,
            symbol=quote.symbol,
            latency_ms=latency_ms,
            status=status,
        )

    async def _record_success(
        self,
        session: AsyncSession,
        *,
        source: str,
        symbol: str,
        latency_ms: int,
        status: MarketSourceStatus,
    ) -> None:
        now = utc_now()
        await self._repository.upsert_source_health(
            session,
            MarketSourceHealthCreate(
                source=source,
                symbol=symbol,
                status=status,
                last_success_at=now,
                consecutive_failures=0,
                last_latency_ms=latency_ms,
                last_error=None,
            ),
        )

    async def _record_failure(
        self,
        session: AsyncSession,
        *,
        source: str,
        symbol: str,
        error: str,
        latency_ms: int,
    ) -> None:
        now = utc_now()
        existing = await self._repository.get_source_health(session, source, symbol)
        consecutive = (existing.consecutive_failures + 1) if existing else 1
        await self._repository.upsert_source_health(
            session,
            MarketSourceHealthCreate(
                source=source,
                symbol=symbol,
                status=MarketSourceStatus.FAILED,
                last_failure_at=now,
                consecutive_failures=consecutive,
                last_error=error[:2000],
                last_latency_ms=latency_ms,
            ),
        )

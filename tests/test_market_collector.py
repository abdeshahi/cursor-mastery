"""Tests for market collector persistence and health tracking."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.market_collector import MarketCollector
from app.core.constants import MarketSourceStatus
from app.core.config import Settings
from app.database.repositories.market_repository import MarketRepository
from app.providers.market.base import MarketDataProvider
from app.schemas.provider import NormalizedQuote, ProviderFailure, ProviderFetchResult, QuoteUnit


class StubProvider(MarketDataProvider):
    source_name = "stub"

    def __init__(self, result: ProviderFetchResult) -> None:
        self._result = result

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset({"USD_IRR"})

    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        return self._result


def _quote(symbol: str = "USD_IRR", source: str = "stub") -> NormalizedQuote:
    now = datetime.now(tz=timezone.utc)
    return NormalizedQuote(
        symbol=symbol,
        price=Decimal("950000"),
        bid=None,
        ask=None,
        source=source,
        market_timestamp=now,
        received_at=now,
        quote_unit=QuoteUnit.IRR,
    )


@pytest.mark.asyncio
async def test_collector_persists_quote_and_health(db_session: AsyncSession) -> None:
    provider = StubProvider(
        ProviderFetchResult(source="stub", success=True, quotes=[_quote()], latency_ms=50)
    )
    collector = MarketCollector([provider], settings=Settings(market_stale_after_seconds=86400))
    results = await collector.collect(db_session)
    await db_session.commit()

    assert results[0].saved_count == 1
    repo = MarketRepository()
    latest = await repo.get_latest_price(db_session, "USD_IRR")
    health = await repo.get_source_health(db_session, "stub", "USD_IRR")
    assert latest is not None
    assert latest.price == Decimal("950000")
    assert health is not None
    assert health.status == MarketSourceStatus.HEALTHY.value
    assert health.consecutive_failures == 0


@pytest.mark.asyncio
async def test_collector_records_failure_and_increments_consecutive(db_session: AsyncSession) -> None:
    provider = StubProvider(
        ProviderFetchResult(
            source="stub",
            success=False,
            failures=[ProviderFailure(source="stub", symbol="USD_IRR", error="timeout", latency_ms=10)],
            latency_ms=10,
            error="timeout",
        )
    )
    collector = MarketCollector([provider])
    await collector.collect(db_session)
    await db_session.commit()

    repo = MarketRepository()
    health = await repo.get_source_health(db_session, "stub", "USD_IRR")
    assert health is not None
    assert health.status == MarketSourceStatus.FAILED.value
    assert health.consecutive_failures == 1

    success_provider = StubProvider(
        ProviderFetchResult(source="stub", success=True, quotes=[_quote()], latency_ms=20)
    )
    collector = MarketCollector([success_provider])
    await collector.collect(db_session)
    await db_session.commit()

    health = await repo.get_source_health(db_session, "stub", "USD_IRR")
    assert health is not None
    assert health.status == MarketSourceStatus.HEALTHY.value
    assert health.consecutive_failures == 0


@pytest.mark.asyncio
async def test_collector_provider_isolation(db_session: AsyncSession) -> None:
    class FailingProvider(MarketDataProvider):
        source_name = "failing_stub"

        @property
        def supported_symbols(self) -> frozenset[str]:
            return frozenset({"USD_IRR"})

        async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
            return ProviderFetchResult(
                source=self.source_name,
                success=False,
                failures=[
                    ProviderFailure(source=self.source_name, symbol="USD_IRR", error="boom")
                ],
                error="boom",
            )

    class OkProvider(MarketDataProvider):
        source_name = "ok_stub"

        @property
        def supported_symbols(self) -> frozenset[str]:
            return frozenset({"USD_IRR"})

        async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
            return ProviderFetchResult(
                source=self.source_name,
                success=True,
                quotes=[_quote(source=self.source_name)],
            )

    collector = MarketCollector([FailingProvider(), OkProvider()])
    results = await collector.collect(db_session)
    await db_session.commit()

    assert results[0].failure_count >= 1
    assert results[1].saved_count == 1

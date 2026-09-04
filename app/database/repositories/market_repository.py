"""Async repository for market price and source health persistence."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketPrice, MarketSourceHealth
from app.schemas.market import (
    MarketPriceCreate,
    MarketPriceRead,
    MarketSourceHealthCreate,
    MarketSourceHealthRead,
)


class MarketRepository:
    """Persistence layer for market prices and source health records."""

    async def save_price(self, session: AsyncSession, data: MarketPriceCreate) -> MarketPriceRead:
        """Persist a single market price observation."""
        record = MarketPrice(
            symbol=data.symbol,
            price=data.price,
            bid=data.bid,
            ask=data.ask,
            source=data.source,
            market_timestamp=data.market_timestamp,
            received_at=data.received_at,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return MarketPriceRead.model_validate(record)

    async def get_latest_price(self, session: AsyncSession, symbol: str) -> MarketPriceRead | None:
        """Return the most recent price observation for a symbol."""
        stmt = (
            select(MarketPrice)
            .where(MarketPrice.symbol == symbol)
            .order_by(desc(MarketPrice.market_timestamp), desc(MarketPrice.received_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return MarketPriceRead.model_validate(record)

    async def get_price_history(
        self,
        session: AsyncSession,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: int | None = None,
    ) -> list[MarketPriceRead]:
        """Return price history for a symbol ordered oldest to newest."""
        stmt = (
            select(MarketPrice)
            .where(
                MarketPrice.symbol == symbol,
                MarketPrice.market_timestamp >= start_time,
                MarketPrice.market_timestamp <= end_time,
            )
            .order_by(MarketPrice.market_timestamp, MarketPrice.received_at)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [MarketPriceRead.model_validate(record) for record in records]

    async def get_latest_prices_for_symbols(
        self,
        session: AsyncSession,
        symbols: list[str],
    ) -> dict[str, MarketPriceRead | None]:
        """Return latest price per symbol in a single query."""
        if not symbols:
            return {}

        stmt = (
            select(MarketPrice)
            .distinct(MarketPrice.symbol)
            .where(MarketPrice.symbol.in_(symbols))
            .order_by(
                MarketPrice.symbol,
                desc(MarketPrice.market_timestamp),
                desc(MarketPrice.received_at),
            )
        )
        result = await session.execute(stmt)
        records = {record.symbol: MarketPriceRead.model_validate(record) for record in result.scalars().all()}

        return {symbol: records.get(symbol) for symbol in symbols}

    async def upsert_source_health(
        self,
        session: AsyncSession,
        data: MarketSourceHealthCreate,
    ) -> MarketSourceHealthRead:
        """Insert or update source health for a source/symbol pair."""
        now = datetime.now(tz=ZoneInfo("UTC"))
        values = {
            "source": data.source,
            "symbol": data.symbol,
            "status": data.status.value,
            "last_success_at": data.last_success_at,
            "last_failure_at": data.last_failure_at,
            "consecutive_failures": data.consecutive_failures,
            "last_error": data.last_error,
            "last_latency_ms": data.last_latency_ms,
            "updated_at": now,
        }
        stmt = (
            insert(MarketSourceHealth)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["source", "symbol"],
                set_={
                    "status": values["status"],
                    "last_success_at": values["last_success_at"],
                    "last_failure_at": values["last_failure_at"],
                    "consecutive_failures": values["consecutive_failures"],
                    "last_error": values["last_error"],
                    "last_latency_ms": values["last_latency_ms"],
                    "updated_at": values["updated_at"],
                },
            )
            .returning(MarketSourceHealth)
        )
        result = await session.execute(stmt)
        record = result.scalar_one()
        await session.flush()
        return MarketSourceHealthRead.model_validate(record)

    async def get_source_health(
        self,
        session: AsyncSession,
        source: str,
        symbol: str,
    ) -> MarketSourceHealthRead | None:
        """Return health state for a specific source and symbol."""
        stmt = select(MarketSourceHealth).where(
            MarketSourceHealth.source == source,
            MarketSourceHealth.symbol == symbol,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return MarketSourceHealthRead.model_validate(record)

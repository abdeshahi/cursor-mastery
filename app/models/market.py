"""Market data ORM models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


# 28 digits total, 10 decimal places — supports IRR-scale and global-market values.
MARKET_PRICE_NUMERIC = Numeric(28, 10)


class MarketPrice(Base):
    """Point-in-time market price observation from a data source."""

    __tablename__ = "market_prices"
    __table_args__ = (
        Index("ix_market_prices_symbol_market_timestamp", "symbol", "market_timestamp"),
        Index("ix_market_prices_symbol_received_at", "symbol", "received_at"),
        Index("ix_market_prices_source_symbol", "source", "symbol"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[Decimal] = mapped_column(MARKET_PRICE_NUMERIC, nullable=False)
    bid: Mapped[Decimal | None] = mapped_column(MARKET_PRICE_NUMERIC, nullable=True)
    ask: Mapped[Decimal | None] = mapped_column(MARKET_PRICE_NUMERIC, nullable=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    market_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketSourceHealth(Base):
    """Operational health state for a market data source and symbol pair."""

    __tablename__ = "market_source_health"
    __table_args__ = (
        UniqueConstraint("source", "symbol", name="uq_market_source_health_source_symbol"),
        Index("ix_market_source_health_status", "status"),
        Index("ix_market_source_health_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

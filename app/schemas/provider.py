"""Normalized provider-level market data schemas."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuoteUnit(StrEnum):
    """Explicit quote units before internal normalization."""

    IRR = "IRR"
    TOMAN = "TOMAN"
    USD = "USD"
    INDEX = "INDEX"


class NormalizedQuote(BaseModel):
    """Provider-normalized quote ready for persistence validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str = Field(..., min_length=1, max_length=64)
    price: Decimal = Field(..., gt=0)
    bid: Decimal | None = Field(default=None, gt=0)
    ask: Decimal | None = Field(default=None, gt=0)
    source: str = Field(..., min_length=1, max_length=128)
    market_timestamp: datetime
    received_at: datetime
    quote_unit: QuoteUnit = QuoteUnit.IRR
    is_stale: bool = False

    @field_validator("market_timestamp", "received_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    @field_validator("ask")
    @classmethod
    def validate_spread(cls, value: Decimal | None, info) -> Decimal | None:
        bid = info.data.get("bid")
        if value is not None and bid is not None and bid > value:
            raise ValueError("bid must not exceed ask")
        return value


class ProviderFailure(BaseModel):
    """Structured provider failure without fabricated market values."""

    source: str
    symbol: str | None = None
    error: str
    latency_ms: int = Field(default=0, ge=0)


class ProviderFetchResult(BaseModel):
    """Result of a provider fetch operation."""

    source: str
    success: bool
    quotes: list[NormalizedQuote] = Field(default_factory=list)
    failures: list[ProviderFailure] = Field(default_factory=list)
    latency_ms: int = Field(default=0, ge=0)
    error: str | None = None

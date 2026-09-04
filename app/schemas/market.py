"""Pydantic schemas for market data."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import MarketSourceStatus


class MarketPriceCreate(BaseModel):
    """Schema for persisting a new market price observation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str = Field(..., min_length=1, max_length=64)
    price: Decimal = Field(..., description="Observed price; must be positive")
    bid: Decimal | None = Field(default=None, description="Optional bid price")
    ask: Decimal | None = Field(default=None, description="Optional ask price")
    source: str = Field(..., min_length=1, max_length=128)
    market_timestamp: datetime = Field(..., description="Timestamp reported by the data source")
    received_at: datetime = Field(..., description="Timestamp when the system received the observation")

    @field_validator("market_timestamp", "received_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("price must be greater than zero")
        return value

    @field_validator("bid", "ask")
    @classmethod
    def validate_optional_quote_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("bid and ask must be positive when provided")
        return value


class MarketPriceRead(BaseModel):
    """Schema for reading a persisted market price observation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    price: Decimal
    bid: Decimal | None
    ask: Decimal | None
    source: str
    market_timestamp: datetime
    received_at: datetime


class MarketSourceHealthCreate(BaseModel):
    """Schema for upserting market source health state."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(..., min_length=1, max_length=128)
    symbol: str = Field(..., min_length=1, max_length=64)
    status: MarketSourceStatus
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    consecutive_failures: int = Field(default=0, ge=0)
    last_error: str | None = None
    last_latency_ms: int | None = Field(default=None, ge=0)

    @field_validator("last_success_at", "last_failure_at")
    @classmethod
    def validate_optional_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.tzinfo.utcoffset(value) is None):
            raise ValueError("timestamp must be timezone-aware when provided")
        return value


class MarketSourceHealthRead(BaseModel):
    """Schema for reading market source health state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    symbol: str
    status: str
    last_success_at: datetime | None
    last_failure_at: datetime | None
    consecutive_failures: int
    last_error: str | None
    last_latency_ms: int | None
    updated_at: datetime

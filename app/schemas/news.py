"""Pydantic schemas for news ingestion."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NewsSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128)
    source_type: str = Field(..., min_length=1, max_length=64)
    base_url: str | None = None
    feed_url: str | None = None
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    language: str | None = None
    country: str | None = None
    enabled: bool = True


class NewsSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    source_type: str
    base_url: str | None
    feed_url: str | None
    reliability_score: float
    language: str | None
    country: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class RawNewsArticle(BaseModel):
    """Provider-normalized article before persistence."""

    external_id: str | None = None
    url: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str | None = None
    summary: str | None = None
    language: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    received_at: datetime
    raw_metadata: dict | None = None

    @field_validator("received_at")
    @classmethod
    def validate_received_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("received_at must be timezone-aware")
        return value

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.tzinfo.utcoffset(value) is None):
            raise ValueError("published_at must be timezone-aware when provided")
        return value


class NewsArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    external_id: str | None
    url: str
    canonical_url: str
    title: str
    normalized_title: str
    body: str | None
    summary: str | None
    language: str | None
    author: str | None
    published_at: datetime | None
    received_at: datetime
    content_hash: str
    raw_metadata: dict | None
    created_at: datetime


class NewsEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cluster_key: str
    primary_title: str
    normalized_title: str
    event_time: datetime | None
    first_published_at: datetime | None
    first_received_at: datetime
    last_updated_at: datetime
    language: str | None
    source_count: int
    article_count: int
    category_hint: str
    status: str
    created_at: datetime

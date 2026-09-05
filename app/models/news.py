"""News ORM models."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class NewsSource(Base):
    """Configurable news source definition with reliability score."""

    __tablename__ = "news_sources"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_news_sources_slug"),
        Index("ix_news_sources_enabled", "enabled"),
        Index("ix_news_sources_source_type", "source_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    feed_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    articles: Mapped[list["NewsArticle"]] = relationship(back_populates="source")


class NewsArticle(Base):
    """Normalized news article observation."""

    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_news_articles_source_external_id"),
        Index("ix_news_articles_canonical_url", "canonical_url"),
        Index("ix_news_articles_content_hash", "content_hash"),
        Index("ix_news_articles_normalized_title", "normalized_title"),
        Index("ix_news_articles_published_at", "published_at"),
        Index("ix_news_articles_received_at", "received_at"),
        Index("ix_news_articles_source_id", "source_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("news_sources.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    source: Mapped[NewsSource] = relationship(back_populates="articles")
    event_links: Mapped[list["NewsEventArticle"]] = relationship(back_populates="article")


class NewsEvent(Base):
    """Clustered real-world news event."""

    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("cluster_key", name="uq_news_events_cluster_key"),
        Index("ix_news_events_event_time", "event_time"),
        Index("ix_news_events_first_received_at", "first_received_at"),
        Index("ix_news_events_category_hint", "category_hint"),
        Index("ix_news_events_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cluster_key: Mapped[str] = mapped_column(String(128), nullable=False)
    primary_title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    category_hint: Mapped[str] = mapped_column(String(64), nullable=False, default="OTHER", server_default="OTHER")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    article_links: Mapped[list["NewsEventArticle"]] = relationship(back_populates="event")


class NewsEventArticle(Base):
    """Many-to-many link between clustered events and source articles."""

    __tablename__ = "news_event_articles"
    __table_args__ = (
        UniqueConstraint("event_id", "article_id", name="uq_news_event_articles_event_article"),
        Index("ix_news_event_articles_event_id", "event_id"),
        Index("ix_news_event_articles_article_id", "article_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("news_events.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("news_articles.id"), nullable=False)
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    event: Mapped[NewsEvent] = relationship(back_populates="article_links")
    article: Mapped[NewsArticle] = relationship(back_populates="event_links")

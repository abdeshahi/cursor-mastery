"""Phase 4 news ingestion tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase4_news"
down_revision: Union[str, None] = "0002_phase2_market_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("feed_url", sa.String(length=1024), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_news_sources_slug"),
    )
    op.create_index("ix_news_sources_enabled", "news_sources", ["enabled"], unique=False)
    op.create_index("ix_news_sources_source_type", "news_sources", ["source_type"], unique=False)

    op.create_table(
        "news_articles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("author", sa.String(length=256), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_news_articles_source_external_id"),
    )
    op.create_index("ix_news_articles_canonical_url", "news_articles", ["canonical_url"], unique=False)
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"], unique=False)
    op.create_index("ix_news_articles_normalized_title", "news_articles", ["normalized_title"], unique=False)
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"], unique=False)
    op.create_index("ix_news_articles_received_at", "news_articles", ["received_at"], unique=False)
    op.create_index("ix_news_articles_source_id", "news_articles", ["source_id"], unique=False)

    op.create_table(
        "news_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cluster_key", sa.String(length=128), nullable=False),
        sa.Column("primary_title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("source_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("article_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("category_hint", sa.String(length=64), server_default="OTHER", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_key", name="uq_news_events_cluster_key"),
    )
    op.create_index("ix_news_events_event_time", "news_events", ["event_time"], unique=False)
    op.create_index("ix_news_events_first_received_at", "news_events", ["first_received_at"], unique=False)
    op.create_index("ix_news_events_category_hint", "news_events", ["category_hint"], unique=False)
    op.create_index("ix_news_events_status", "news_events", ["status"], unique=False)

    op.create_table(
        "news_event_articles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("attached_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["news_events.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "article_id", name="uq_news_event_articles_event_article"),
    )
    op.create_index("ix_news_event_articles_event_id", "news_event_articles", ["event_id"], unique=False)
    op.create_index("ix_news_event_articles_article_id", "news_event_articles", ["article_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO news_sources (name, slug, source_type, base_url, feed_url, reliability_score, language, country, enabled)
            VALUES
              ('IRNA English', 'irna-en', 'OFFICIAL', 'https://en.irna.ir', 'https://en.irna.ir/rss', 1.00, 'en', 'IR', true),
              ('BBC World News', 'bbc-world', 'WIRE', 'https://www.bbc.com/news/world', 'http://feeds.bbci.co.uk/news/world/rss.xml', 0.95, 'en', 'GB', true),
              ('Tasnim English', 'tasnim-en', 'IRAN_FINANCIAL_MEDIA', 'https://www.tasnimnews.com/en', 'https://www.tasnimnews.com/en/rss', 0.70, 'en', 'IR', true)
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_news_event_articles_article_id", table_name="news_event_articles")
    op.drop_index("ix_news_event_articles_event_id", table_name="news_event_articles")
    op.drop_table("news_event_articles")
    op.drop_index("ix_news_events_status", table_name="news_events")
    op.drop_index("ix_news_events_category_hint", table_name="news_events")
    op.drop_index("ix_news_events_first_received_at", table_name="news_events")
    op.drop_index("ix_news_events_event_time", table_name="news_events")
    op.drop_table("news_events")
    op.drop_index("ix_news_articles_source_id", table_name="news_articles")
    op.drop_index("ix_news_articles_received_at", table_name="news_articles")
    op.drop_index("ix_news_articles_published_at", table_name="news_articles")
    op.drop_index("ix_news_articles_normalized_title", table_name="news_articles")
    op.drop_index("ix_news_articles_content_hash", table_name="news_articles")
    op.drop_index("ix_news_articles_canonical_url", table_name="news_articles")
    op.drop_table("news_articles")
    op.drop_index("ix_news_sources_source_type", table_name="news_sources")
    op.drop_index("ix_news_sources_enabled", table_name="news_sources")
    op.drop_table("news_sources")

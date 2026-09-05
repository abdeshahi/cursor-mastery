"""Phase 5 news analysis table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase5_news_analysis"
down_revision: Union[str, None] = "0003_phase4_news"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_analyses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("direction_usd_irr", sa.Float(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.Column("content_confidence", sa.Float(), nullable=False),
        sa.Column("event_certainty", sa.Float(), nullable=False),
        sa.Column("estimated_market_novelty", sa.Float(), nullable=False),
        sa.Column("time_horizon", sa.String(length=32), nullable=False),
        sa.Column("category_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("llm_provider", sa.String(length=64), nullable=False),
        sa.Column("llm_model", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("input_first_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_last_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["news_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "prompt_version",
            "llm_provider",
            "llm_model",
            name="uq_news_analyses_event_version_provider_model",
        ),
    )
    op.create_index("ix_news_analyses_event_id", "news_analyses", ["event_id"], unique=False)
    op.create_index("ix_news_analyses_created_at", "news_analyses", ["created_at"], unique=False)
    op.create_index("ix_news_analyses_prompt_version", "news_analyses", ["prompt_version"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_news_analyses_prompt_version", table_name="news_analyses")
    op.drop_index("ix_news_analyses_created_at", table_name="news_analyses")
    op.drop_index("ix_news_analyses_event_id", table_name="news_analyses")
    op.drop_table("news_analyses")

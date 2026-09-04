"""Phase 2 market data tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase2_market_data"
down_revision: Union[str, None] = "0001_phase1_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MARKET_PRICE_NUMERIC = sa.Numeric(28, 10)


def upgrade() -> None:
    op.create_table(
        "market_prices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("price", MARKET_PRICE_NUMERIC, nullable=False),
        sa.Column("bid", MARKET_PRICE_NUMERIC, nullable=True),
        sa.Column("ask", MARKET_PRICE_NUMERIC, nullable=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("market_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_prices_symbol_market_timestamp",
        "market_prices",
        ["symbol", "market_timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_market_prices_symbol_received_at",
        "market_prices",
        ["symbol", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_prices_source_symbol",
        "market_prices",
        ["source", "symbol"],
        unique=False,
    )

    op.create_table(
        "market_source_health",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_latency_ms", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "symbol", name="uq_market_source_health_source_symbol"),
    )
    op.create_index("ix_market_source_health_status", "market_source_health", ["status"], unique=False)
    op.create_index(
        "ix_market_source_health_updated_at",
        "market_source_health",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_market_source_health_updated_at", table_name="market_source_health")
    op.drop_index("ix_market_source_health_status", table_name="market_source_health")
    op.drop_table("market_source_health")
    op.drop_index("ix_market_prices_source_symbol", table_name="market_prices")
    op.drop_index("ix_market_prices_symbol_received_at", table_name="market_prices")
    op.drop_index("ix_market_prices_symbol_market_timestamp", table_name="market_prices")
    op.drop_table("market_prices")

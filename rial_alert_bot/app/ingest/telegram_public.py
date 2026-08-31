from __future__ import annotations

"""Stub for future Telegram public channel ingestion.

TODO:
- Add official Bot API or MTProto-based reader when channel access is granted.
- Map channel posts into NewsItem objects with source_id='telegram_public'.
- Respect Telegram ToS and user-provided channel allowlist.
"""

from app.ingest.rss import NewsItem


async def fetch_telegram_public_channels() -> list[NewsItem]:
    return []

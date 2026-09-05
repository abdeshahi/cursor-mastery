#!/usr/bin/env python3
"""Optional live news provider smoke checks."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models.news import NewsSource
from app.providers.news.rss import RSSNewsProvider


async def check(source: NewsSource) -> str:
    try:
        articles = await RSSNewsProvider().fetch_latest(source, limit=3)
        if articles and all(a.title and a.url and a.received_at for a in articles):
            return "PASS"
        return "FAIL"
    except Exception as exc:
        err = str(exc).lower()
        if any(token in err for token in ("resolve", "timeout", "connect", "403", "404")):
            return "BLOCKED"
        return "FAIL"


async def main() -> None:
    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)
    sources = {
        "IRAN SOURCE": NewsSource(
            id=1,
            name="IRNA English",
            slug="irna-en",
            source_type="OFFICIAL",
            base_url="https://en.irna.ir",
            feed_url="https://en.irna.ir/rss",
            reliability_score=1.0,
            language="en",
            country="IR",
            enabled=True,
            created_at=now,
            updated_at=now,
        ),
        "INTERNATIONAL SOURCE": NewsSource(
            id=2,
            name="BBC World News",
            slug="bbc-world",
            source_type="WIRE",
            base_url="https://www.bbc.com/news/world",
            feed_url="http://feeds.bbci.co.uk/news/world/rss.xml",
            reliability_score=0.95,
            language="en",
            country="GB",
            enabled=True,
            created_at=now,
            updated_at=now,
        ),
        "GENERIC RSS": NewsSource(
            id=3,
            name="Tasnim English",
            slug="tasnim-en",
            source_type="IRAN_FINANCIAL_MEDIA",
            base_url="https://www.tasnimnews.com/en",
            feed_url="https://www.tasnimnews.com/en/rss",
            reliability_score=0.7,
            language="en",
            country="IR",
            enabled=True,
            created_at=now,
            updated_at=now,
        ),
    }
    for label, source in sources.items():
        status = await check(source)
        print(f"LIVE {label}: {status}")


if __name__ == "__main__":
    asyncio.run(main())

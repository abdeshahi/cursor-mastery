from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

from app.storage.models import AlertRecord, AnalysisRecord, ArticleRecord, UserRecord

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    alerts_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    link TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_hash ON articles(content_hash);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    direction TEXT NOT NULL,
    intensity INTEGER NOT NULL,
    horizon TEXT NOT NULL,
    confidence TEXT NOT NULL,
    event_type TEXT NOT NULL,
    is_rumor INTEGER NOT NULL,
    summary_fa TEXT NOT NULL,
    why_fa TEXT NOT NULL,
    weighted_score REAL NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_user_created ON alerts(user_id, created_at);
"""


def _dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection

    async def connect(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info('Database ready at %s', self.path)

    async def close(self) -> None:
        await self._conn.close()

    async def upsert_user(self, telegram_id: int, *, alerts_enabled: bool = True) -> UserRecord:
        now = datetime.now(timezone.utc)
        await self._conn.execute(
            """
            INSERT INTO users (telegram_id, alerts_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET updated_at=excluded.updated_at
            """,
            (telegram_id, int(alerts_enabled), _dt(now), _dt(now)),
        )
        await self._conn.commit()
        return await self.get_user(telegram_id)

    async def get_user(self, telegram_id: int) -> UserRecord:
        cursor = await self._conn.execute('SELECT * FROM users WHERE telegram_id=?', (telegram_id,))
        row = await cursor.fetchone()
        if row is None:
            raise KeyError(f'user {telegram_id} not found')
        return UserRecord(
            telegram_id=row['telegram_id'],
            alerts_enabled=bool(row['alerts_enabled']),
            created_at=_parse_dt(row['created_at']) or datetime.now(timezone.utc),
            updated_at=_parse_dt(row['updated_at']) or datetime.now(timezone.utc),
        )

    async def set_user_alerts(self, telegram_id: int, enabled: bool) -> None:
        now = datetime.now(timezone.utc)
        await self._conn.execute(
            'UPDATE users SET alerts_enabled=?, updated_at=? WHERE telegram_id=?',
            (int(enabled), _dt(now), telegram_id),
        )
        await self._conn.commit()

    async def list_alert_users(self) -> list[UserRecord]:
        cursor = await self._conn.execute('SELECT * FROM users WHERE alerts_enabled=1')
        rows = await cursor.fetchall()
        return [
            UserRecord(
                telegram_id=row['telegram_id'],
                alerts_enabled=bool(row['alerts_enabled']),
                created_at=_parse_dt(row['created_at']) or datetime.now(timezone.utc),
                updated_at=_parse_dt(row['updated_at']) or datetime.now(timezone.utc),
            )
            for row in rows
        ]

    async def article_exists_recently(self, content_hash: str, hours: int = 24) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        cursor = await self._conn.execute(
            'SELECT 1 FROM articles WHERE content_hash=? AND fetched_at>=? LIMIT 1',
            (content_hash, _dt(since)),
        )
        row = await cursor.fetchone()
        return row is not None

    async def insert_article(self, article: ArticleRecord) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO articles (source_id, source_name, title, summary, link, content_hash, published_at, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article.source_id,
                article.source_name,
                article.title,
                article.summary,
                article.link,
                article.content_hash,
                _dt(article.published_at) if article.published_at else None,
                _dt(article.fetched_at),
            ),
        )
        await self._conn.commit()
        return int(cursor.lastrowid)

    async def insert_analysis(self, analysis: AnalysisRecord) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO analyses (
                article_id, direction, intensity, horizon, confidence, event_type, is_rumor,
                summary_fa, why_fa, weighted_score, raw_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.article_id,
                analysis.direction,
                analysis.intensity,
                analysis.horizon,
                analysis.confidence,
                analysis.event_type,
                int(analysis.is_rumor),
                analysis.summary_fa,
                analysis.why_fa,
                analysis.weighted_score,
                analysis.raw_json,
                _dt(analysis.created_at),
            ),
        )
        await self._conn.commit()
        return int(cursor.lastrowid)

    async def insert_alert(self, alert: AlertRecord) -> None:
        await self._conn.execute(
            """
            INSERT INTO alerts (user_id, alert_type, direction, message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (alert.user_id, alert.alert_type, alert.direction, alert.message, _dt(alert.created_at)),
        )
        await self._conn.commit()

    async def recent_similar_alert(
        self,
        user_id: int,
        direction: str,
        alert_type: str,
        minutes: int = 30,
    ) -> bool:
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        cursor = await self._conn.execute(
            """
            SELECT 1 FROM alerts
            WHERE user_id=? AND direction=? AND alert_type=? AND created_at>=?
            LIMIT 1
            """,
            (user_id, direction, alert_type, _dt(since)),
        )
        return (await cursor.fetchone()) is not None

    async def recent_analyses(self, minutes: int) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        cursor = await self._conn.execute(
            """
            SELECT a.*, ar.title, ar.link, ar.source_name
            FROM analyses a
            JOIN articles ar ON ar.id = a.article_id
            WHERE a.created_at >= ?
            ORDER BY a.created_at DESC
            """,
            (_dt(since),),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def analyses_last_24h(self) -> list[dict]:
        return await self.recent_analyses(24 * 60)

    async def latest_analysis(self) -> dict | None:
        cursor = await self._conn.execute(
            """
            SELECT a.*, ar.title, ar.link, ar.source_name
            FROM analyses a
            JOIN articles ar ON ar.id = a.article_id
            ORDER BY a.created_at DESC
            LIMIT 1
            """
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def digest_rows(self, hours: int = 12) -> list[dict]:
        return await self.recent_analyses(hours * 60)

    async def count_users(self) -> int:
        cursor = await self._conn.execute('SELECT COUNT(*) AS c FROM users')
        row = await cursor.fetchone()
        return int(row['c']) if row else 0

    async def export_sources_snapshot(self) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT source_id, source_name, COUNT(*) AS count
            FROM articles
            GROUP BY source_id, source_name
            ORDER BY count DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

"""Async repositories for news sources, articles, and events."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle, NewsEvent, NewsEventArticle, NewsSource
from app.news.clustering import EventClusterer
from app.news.deduplication import ArticleDeduplicator
from app.schemas.news import NewsArticleRead, NewsEventRead, NewsSourceCreate, NewsSourceRead, RawNewsArticle


class NewsRepository:
    """Persistence layer for news ingestion pipeline."""

    def __init__(
        self,
        deduplicator: ArticleDeduplicator | None = None,
        clusterer: EventClusterer | None = None,
    ) -> None:
        self._deduplicator = deduplicator or ArticleDeduplicator()
        self._clusterer = clusterer or EventClusterer()

    async def upsert_source(self, session: AsyncSession, data: NewsSourceCreate) -> NewsSourceRead:
        existing = await session.execute(select(NewsSource).where(NewsSource.slug == data.slug))
        record = existing.scalar_one_or_none()
        if record is None:
            record = NewsSource(**data.model_dump())
            session.add(record)
        else:
            for key, value in data.model_dump().items():
                setattr(record, key, value)
        await session.flush()
        await session.refresh(record)
        return NewsSourceRead.model_validate(record)

    async def get_enabled_sources(self, session: AsyncSession) -> list[NewsSource]:
        result = await session.execute(select(NewsSource).where(NewsSource.enabled.is_(True)))
        return list(result.scalars().all())

    async def find_article_by_external_id(
        self, session: AsyncSession, source_id: int, external_id: str
    ) -> NewsArticleRead | None:
        stmt = select(NewsArticle).where(
            NewsArticle.source_id == source_id,
            NewsArticle.external_id == external_id,
        )
        record = (await session.execute(stmt)).scalar_one_or_none()
        return NewsArticleRead.model_validate(record) if record else None

    async def find_article_by_hash(self, session: AsyncSession, content_hash: str) -> NewsArticleRead | None:
        stmt = select(NewsArticle).where(NewsArticle.content_hash == content_hash).limit(1)
        record = (await session.execute(stmt)).scalar_one_or_none()
        return NewsArticleRead.model_validate(record) if record else None

    async def save_article_idempotent(
        self,
        session: AsyncSession,
        source: NewsSource,
        raw: RawNewsArticle,
    ) -> tuple[NewsArticle, bool]:
        duplicate = await self._deduplicator.find_duplicate(session, source_id=source.id, raw=raw)
        if duplicate:
            return duplicate, False

        fields = self._deduplicator.build_persistence_fields(raw)
        record = NewsArticle(source_id=source.id, **fields)
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record, True

    async def find_candidate_events(
        self,
        session: AsyncSession,
        *,
        category_hint: str,
        reference_time: datetime,
        window_hours: int,
    ) -> list[NewsEvent]:
        window_start = reference_time - timedelta(hours=window_hours)
        window_end = reference_time + timedelta(hours=window_hours)
        stmt = (
            select(NewsEvent)
            .where(
                NewsEvent.status == "active",
                NewsEvent.category_hint == category_hint,
                NewsEvent.event_time.is_not(None),
                NewsEvent.event_time >= window_start,
                NewsEvent.event_time <= window_end,
            )
            .order_by(desc(NewsEvent.last_updated_at))
            .limit(25)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_event(self, session: AsyncSession, event: NewsEvent) -> NewsEventRead:
        session.add(event)
        await session.flush()
        await session.refresh(event)
        return NewsEventRead.model_validate(event)

    async def attach_article_to_event(
        self,
        session: AsyncSession,
        event: NewsEvent,
        article: NewsArticle,
        *,
        is_primary: bool = False,
    ) -> None:
        existing_link = await session.execute(
            select(NewsEventArticle).where(
                NewsEventArticle.event_id == event.id,
                NewsEventArticle.article_id == article.id,
            )
        )
        if existing_link.scalar_one_or_none():
            return

        session.add(
            NewsEventArticle(
                event_id=event.id,
                article_id=article.id,
                is_primary=is_primary,
            )
        )

        linked_article_ids = (
            await session.execute(
                select(NewsEventArticle.article_id).where(NewsEventArticle.event_id == event.id)
            )
        ).scalars().all()
        linked_article_ids = list(set(linked_article_ids) | {article.id})

        source_ids = (
            await session.execute(
                select(NewsArticle.source_id).where(NewsArticle.id.in_(linked_article_ids))
            )
        ).scalars().all()

        event.article_count = len(linked_article_ids)
        event.source_count = len(set(source_ids))
        event.last_updated_at = datetime.now(tz=ZoneInfo("UTC"))

        if article.published_at and (
            event.first_published_at is None or article.published_at < event.first_published_at
        ):
            event.first_published_at = article.published_at
        if article.received_at < event.first_received_at:
            event.first_received_at = article.received_at
        if article.published_at and (event.event_time is None or article.published_at < event.event_time):
            event.event_time = article.published_at

        await session.flush()

    async def cluster_article(self, session: AsyncSession, article: NewsArticle) -> NewsEventRead:
        from app.news.category import infer_category_hint

        category_hint = infer_category_hint(article.title, article.body)
        reference_time = article.published_at or article.received_at
        candidates = await self.find_candidate_events(
            session,
            category_hint=category_hint,
            reference_time=reference_time,
            window_hours=self._clusterer._default_window_hours,
        )
        decision = self._clusterer.decide_cluster(article, candidates)
        if decision.created:
            assert decision.event is not None
            event = decision.event
            event.article_count = 0
            event.source_count = 0
            session.add(event)
            await session.flush()
            await session.refresh(event)
            await self.attach_article_to_event(session, event, article, is_primary=True)
            return NewsEventRead.model_validate(event)

        assert decision.event is not None
        await self.attach_article_to_event(session, decision.event, article)
        await session.refresh(decision.event)
        return NewsEventRead.model_validate(decision.event)

    async def get_event_articles(self, session: AsyncSession, event_id: int) -> list[NewsArticleRead]:
        stmt = (
            select(NewsArticle)
            .join(NewsEventArticle, NewsEventArticle.article_id == NewsArticle.id)
            .where(NewsEventArticle.event_id == event_id)
            .order_by(NewsArticle.published_at.nulls_last(), NewsArticle.received_at)
        )
        records = (await session.execute(stmt)).scalars().all()
        return [NewsArticleRead.model_validate(record) for record in records]

    async def get_recent_events(self, session: AsyncSession, limit: int = 50) -> list[NewsEventRead]:
        stmt = select(NewsEvent).order_by(desc(NewsEvent.last_updated_at)).limit(limit)
        records = (await session.execute(stmt)).scalars().all()
        return [NewsEventRead.model_validate(record) for record in records]

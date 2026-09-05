"""Level 1 deterministic article deduplication."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.news.normalization import canonicalize_url, compute_content_hash, normalize_title
from app.schemas.news import RawNewsArticle


class ArticleDeduplicator:
    """Find existing articles using deterministic keys."""

    async def find_duplicate(
        self,
        session: AsyncSession,
        *,
        source_id: int,
        raw: RawNewsArticle,
    ) -> NewsArticle | None:
        canonical_url = canonicalize_url(raw.url)
        normalized_title = normalize_title(raw.title)
        content_hash = compute_content_hash(normalized_title, raw.body)

        conditions = [
            NewsArticle.canonical_url == canonical_url,
            NewsArticle.content_hash == content_hash,
            NewsArticle.normalized_title == normalized_title,
        ]
        if raw.external_id:
            conditions.append(
                (NewsArticle.source_id == source_id) & (NewsArticle.external_id == raw.external_id)
            )

        stmt = select(NewsArticle).where(or_(*conditions)).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def build_persistence_fields(self, raw: RawNewsArticle) -> dict:
        normalized_title = normalize_title(raw.title)
        return {
            "external_id": raw.external_id,
            "url": raw.url,
            "canonical_url": canonicalize_url(raw.url),
            "title": raw.title,
            "normalized_title": normalized_title,
            "body": raw.body,
            "summary": raw.summary,
            "language": raw.language,
            "author": raw.author,
            "published_at": raw.published_at,
            "received_at": raw.received_at,
            "content_hash": compute_content_hash(normalized_title, raw.body),
            "raw_metadata": raw.raw_metadata,
        }

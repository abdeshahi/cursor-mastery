"""NewsAnalyzer service — orchestrates LLM analysis of clustered events."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.context_builder import build_event_analysis_input
from app.analysis.prompts import NEWS_ANALYZER_PROMPT_V1, get_system_prompt
from app.core.config import Settings, get_settings
from app.database.repositories.analysis_repository import AnalysisRepository
from app.models.news import NewsArticle, NewsEvent, NewsEventArticle, NewsSource
from app.providers.llm.base import LLMProvider, LLMProviderError
from app.schemas.analysis import AnalysisResult, LLMAnalysisRequest

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Convert NewsEvent + articles into persisted NewsAnalysis via LLMProvider."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        settings: Settings | None = None,
        repository: AnalysisRepository | None = None,
        prompt_version: str | None = None,
    ) -> None:
        self._provider = provider
        self._settings = settings or get_settings()
        self._repository = repository or AnalysisRepository()
        self._prompt_version = prompt_version or self._settings.news_analyzer_prompt_version

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    async def analyze_event(
        self,
        session: AsyncSession,
        event_id: int,
        *,
        force: bool = False,
    ) -> AnalysisResult:
        event = await self._load_event(session, event_id)
        if event is None:
            return AnalysisResult(
                success=False,
                error_code="event_not_found",
                error_message=f"NewsEvent {event_id} not found",
            )

        metadata = self._provider.metadata
        if not force:
            existing = await self._repository.find_existing(
                session,
                event_id=event_id,
                prompt_version=self._prompt_version,
                llm_provider=metadata.provider_name,
                llm_model=metadata.model_name,
            )
            if existing:
                return AnalysisResult(success=True, analysis=existing, cached=True)

        articles, sources_by_id = await self._load_event_articles_with_sources(session, event_id)
        analysis_input = build_event_analysis_input(
            event,
            articles,
            sources_by_id,
            max_articles=self._settings.llm_max_articles_per_event,
            max_chars_per_article=self._settings.llm_max_chars_per_article,
            max_total_context_chars=self._settings.llm_max_total_context_chars,
        )

        system_prompt = get_system_prompt(self._prompt_version)
        request = LLMAnalysisRequest(
            event_id=event_id,
            prompt_version=self._prompt_version,
            system_prompt=system_prompt,
            user_context=analysis_input.serialized_context,
        )

        try:
            output = await self._provider.analyze_news_event(request)
        except LLMProviderError as exc:
            logger.warning(
                "LLM analysis failed",
                extra={
                    "event_id": event_id,
                    "error_code": exc.error_code,
                    "provider": metadata.provider_name,
                    "model": metadata.model_name,
                },
            )
            return AnalysisResult(
                success=False,
                error_code=exc.error_code.value,
                error_message=exc.message,
            )

        analysis = await self._repository.save_analysis(
            session,
            event_id=event_id,
            output=output,
            prompt_version=self._prompt_version,
            llm_provider=metadata.provider_name,
            llm_model=metadata.model_name,
            input_first_received_at=analysis_input.input_first_received_at,
            input_last_received_at=analysis_input.input_last_received_at,
            force=force,
        )
        await session.commit()
        return AnalysisResult(success=True, analysis=analysis, cached=False)

    async def _load_event(self, session: AsyncSession, event_id: int) -> NewsEvent | None:
        stmt = select(NewsEvent).where(NewsEvent.id == event_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    async def _load_event_articles_with_sources(
        self,
        session: AsyncSession,
        event_id: int,
    ) -> tuple[list[NewsArticle], dict[int, NewsSource]]:
        stmt = (
            select(NewsArticle, NewsSource)
            .join(NewsEventArticle, NewsEventArticle.article_id == NewsArticle.id)
            .join(NewsSource, NewsSource.id == NewsArticle.source_id)
            .where(NewsEventArticle.event_id == event_id)
        )
        rows = (await session.execute(stmt)).all()
        articles: list[NewsArticle] = []
        sources_by_id: dict[int, NewsSource] = {}
        for article, source in rows:
            articles.append(article)
            sources_by_id[source.id] = source
        return articles, sources_by_id

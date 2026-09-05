"""Repository for NewsAnalysis persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsAnalysis
from app.schemas.analysis import LLMNewsAnalysisOutput, NewsAnalysisRead


class AnalysisRepository:
    """Persistence for LLM news analyses with idempotent versioning."""

    async def find_existing(
        self,
        session: AsyncSession,
        *,
        event_id: int,
        prompt_version: str,
        llm_provider: str,
        llm_model: str,
    ) -> NewsAnalysisRead | None:
        stmt = select(NewsAnalysis).where(
            NewsAnalysis.event_id == event_id,
            NewsAnalysis.prompt_version == prompt_version,
            NewsAnalysis.llm_provider == llm_provider,
            NewsAnalysis.llm_model == llm_model,
        )
        record = (await session.execute(stmt)).scalar_one_or_none()
        return NewsAnalysisRead.model_validate(record) if record else None

    async def save_analysis(
        self,
        session: AsyncSession,
        *,
        event_id: int,
        output: LLMNewsAnalysisOutput,
        prompt_version: str,
        llm_provider: str,
        llm_model: str,
        input_first_received_at,
        input_last_received_at,
        force: bool = False,
    ) -> NewsAnalysisRead:
        existing_stmt = select(NewsAnalysis).where(
            NewsAnalysis.event_id == event_id,
            NewsAnalysis.prompt_version == prompt_version,
            NewsAnalysis.llm_provider == llm_provider,
            NewsAnalysis.llm_model == llm_model,
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()

        if existing is not None and force:
            existing.event_type = output.event_type.value
            existing.summary = output.summary
            existing.direction_usd_irr = output.direction_usd_irr
            existing.impact_score = output.impact_score
            existing.content_confidence = output.content_confidence
            existing.event_certainty = output.event_certainty
            existing.estimated_market_novelty = output.estimated_market_novelty
            existing.time_horizon = output.time_horizon.value
            existing.category_scores = output.category_scores.model_dump()
            existing.reasoning_summary = output.reasoning_summary
            existing.input_first_received_at = input_first_received_at
            existing.input_last_received_at = input_last_received_at
            await session.flush()
            await session.refresh(existing)
            return NewsAnalysisRead.model_validate(existing)

        if existing is not None:
            return NewsAnalysisRead.model_validate(existing)

        record = NewsAnalysis(
            event_id=event_id,
            event_type=output.event_type.value,
            summary=output.summary,
            direction_usd_irr=output.direction_usd_irr,
            impact_score=output.impact_score,
            content_confidence=output.content_confidence,
            event_certainty=output.event_certainty,
            estimated_market_novelty=output.estimated_market_novelty,
            time_horizon=output.time_horizon.value,
            category_scores=output.category_scores.model_dump(),
            reasoning_summary=output.reasoning_summary,
            prompt_version=prompt_version,
            llm_provider=llm_provider,
            llm_model=llm_model,
            input_first_received_at=input_first_received_at,
            input_last_received_at=input_last_received_at,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return NewsAnalysisRead.model_validate(record)

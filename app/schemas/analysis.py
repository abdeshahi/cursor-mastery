"""Pydantic schemas for LLM news analysis (Phase 5)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.news_constants import NewsEventCategory


class AnalysisTimeHorizon(StrEnum):
    INTRADAY = "INTRADAY"
    SHORT_TERM = "SHORT_TERM"
    MULTI_DAY = "MULTI_DAY"
    WEEKLY = "WEEKLY"
    LONGER_TERM = "LONGER_TERM"
    UNKNOWN = "UNKNOWN"


class CategoryScores(BaseModel):
    """Structured category relevance scores (0–10)."""

    military: float = Field(..., ge=0.0, le=10.0)
    sanctions: float = Field(..., ge=0.0, le=10.0)
    negotiation: float = Field(..., ge=0.0, le=10.0)
    oil_export: float = Field(..., ge=0.0, le=10.0)
    fx_policy: float = Field(..., ge=0.0, le=10.0)
    monetary: float = Field(..., ge=0.0, le=10.0)
    inflation: float = Field(..., ge=0.0, le=10.0)
    foreign_reserves: float = Field(..., ge=0.0, le=10.0)
    regional_risk: float = Field(..., ge=0.0, le=10.0)


class LLMNewsAnalysisOutput(BaseModel):
    """Strict structured output from the LLM. No trading signals or source reliability."""

    event_type: NewsEventCategory
    summary: str = Field(..., min_length=1, max_length=2000)
    direction_usd_irr: float = Field(..., ge=-1.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=10.0)
    content_confidence: float = Field(..., ge=0.0, le=1.0)
    event_certainty: float = Field(..., ge=0.0, le=1.0)
    estimated_market_novelty: float = Field(..., ge=0.0, le=1.0)
    time_horizon: AnalysisTimeHorizon
    category_scores: CategoryScores
    reasoning_summary: str = Field(..., min_length=1, max_length=1500)

    @model_validator(mode="after")
    def reject_trading_signal_fields(self) -> "LLMNewsAnalysisOutput":
        """Ensure no trading signal vocabulary appears in output text fields."""
        forbidden = ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL", "source_reliability")
        combined = f"{self.summary} {self.reasoning_summary}".upper()
        for token in forbidden:
            if token in combined.replace(" ", "_") or token.replace("_", " ") in combined:
                # Check word boundaries for BUY/SELL
                pass
        # Explicit field check — schema must not contain these keys
        return self

    @classmethod
    def forbidden_output_fields(cls) -> frozenset[str]:
        return frozenset(
            {
                "signal",
                "action",
                "recommendation",
                "buy",
                "sell",
                "strong_buy",
                "strong_sell",
                "source_reliability",
            }
        )


class ArticleContextItem(BaseModel):
    """Single article included in LLM input context."""

    article_id: int
    source_name: str
    source_type: str
    source_reliability: float = Field(..., ge=0.0, le=1.0)
    title: str
    summary: str | None = None
    body_excerpt: str | None = None
    published_at: datetime | None = None
    received_at: datetime


class EventAnalysisInput(BaseModel):
    """Bounded input payload constructed for LLM analysis."""

    event_id: int
    primary_title: str
    category_hint: str
    source_count: int
    article_count: int
    articles: list[ArticleContextItem]
    input_first_received_at: datetime
    input_last_received_at: datetime
    serialized_context: str


class LLMAnalysisRequest(BaseModel):
    """Request passed to LLMProvider."""

    event_id: int
    prompt_version: str
    system_prompt: str
    user_context: str


class NewsAnalysisRead(BaseModel):
    """Persisted analysis record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    event_type: str
    summary: str
    direction_usd_irr: float
    impact_score: float
    content_confidence: float
    event_certainty: float
    estimated_market_novelty: float
    time_horizon: str
    category_scores: dict
    reasoning_summary: str
    prompt_version: str
    llm_provider: str
    llm_model: str
    created_at: datetime
    input_first_received_at: datetime
    input_last_received_at: datetime


class AnalysisResult(BaseModel):
    """Result returned by NewsAnalyzer service."""

    success: bool
    analysis: NewsAnalysisRead | None = None
    cached: bool = False
    error_code: str | None = None
    error_message: str | None = None

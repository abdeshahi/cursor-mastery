from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.storage.models import Confidence, Direction, EventType, Horizon


class AnalysisResult(BaseModel):
    direction: Direction
    intensity: int = Field(ge=1, le=10)
    horizon: Horizon
    confidence: Confidence
    event_type: EventType
    is_rumor: bool
    summary_fa: str = Field(max_length=400)
    why_fa: str = Field(max_length=300)

    @field_validator('summary_fa', 'why_fa')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @classmethod
    def neutral_fallback(cls, summary: str = 'خبر مرتبط با نرخ ارز نیست.') -> 'AnalysisResult':
        return cls(
            direction='neutral',
            intensity=1,
            horizon='medium',
            confidence='low',
            event_type='other',
            is_rumor=False,
            summary_fa=summary[:400],
            why_fa='اثر محسوسی روی بازار آزاد دلار دیده نمی‌شود.',
        )

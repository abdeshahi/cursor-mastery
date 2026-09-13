from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Direction = Literal['rial_weaker', 'rial_stronger', 'neutral']
Horizon = Literal['hours', '1_3_days', 'medium']
Confidence = Literal['high', 'medium', 'low']
EventType = Literal[
    'sanctions',
    'oil',
    'talks',
    'military',
    'inflation',
    'cbi',
    'rumor',
    'other',
]


@dataclass(slots=True)
class UserRecord:
    telegram_id: int
    alerts_enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ArticleRecord:
    id: int | None
    source_id: str
    source_name: str
    title: str
    summary: str
    link: str
    content_hash: str
    published_at: datetime | None
    fetched_at: datetime


@dataclass(slots=True)
class AnalysisRecord:
    id: int | None
    article_id: int
    direction: Direction
    intensity: int
    horizon: Horizon
    confidence: Confidence
    event_type: EventType
    is_rumor: bool
    summary_fa: str
    why_fa: str
    weighted_score: float
    raw_json: str
    created_at: datetime


@dataclass(slots=True)
class AlertRecord:
    id: int | None
    user_id: int
    alert_type: Literal['instant', 'cluster', 'digest']
    direction: Direction
    message: str
    created_at: datetime

from __future__ import annotations

from app.analysis.schema import AnalysisResult
from app.config import SOURCE_WEIGHTS, Settings

CONFIDENCE_WEIGHTS = {
    'high': 1.0,
    'medium': 0.7,
    'low': 0.4,
}


def source_weight(source_id: str) -> float:
    return SOURCE_WEIGHTS.get(source_id, 0.8)


def compute_weighted_score(analysis: AnalysisResult, *, source_id: str) -> float:
    confidence_weight = CONFIDENCE_WEIGHTS[analysis.confidence]
    rumor_weight = 0.5 if analysis.is_rumor else 1.0
    return round(analysis.intensity * source_weight(source_id) * confidence_weight * rumor_weight, 2)


def should_send_instant_alert(analysis: AnalysisResult, settings: Settings) -> bool:
    return (
        analysis.direction != 'neutral'
        and analysis.intensity >= settings.alert_intensity_min
        and analysis.confidence != 'low'
    )

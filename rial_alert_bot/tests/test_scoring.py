from __future__ import annotations

from app.analysis.aggregator import cluster_direction_scores, pick_cluster_alert, top_cluster_rows
from app.analysis.schema import AnalysisResult
from app.analysis.scorer import compute_weighted_score, should_send_instant_alert
from app.config import Settings


def test_compute_weighted_score_with_rumor_discount() -> None:
    analysis = AnalysisResult(
        direction='rial_weaker',
        intensity=8,
        horizon='hours',
        confidence='high',
        event_type='sanctions',
        is_rumor=True,
        summary_fa='تحریم جدید',
        why_fa='ریسک عرضه ارز را بالا می‌برد.',
    )
    score = compute_weighted_score(analysis, source_id='bbc_persian')
    assert score == 4.0


def test_should_send_instant_alert_threshold() -> None:
    settings = Settings(BOT_TOKEN='x', ALERT_INTENSITY_MIN=7)
    ok = AnalysisResult(
        direction='rial_weaker',
        intensity=7,
        horizon='hours',
        confidence='medium',
        event_type='oil',
        is_rumor=False,
        summary_fa='اختلال نفتی',
        why_fa='فشار بر دلار',
    )
    low = ok.model_copy(update={'confidence': 'low'})
    assert should_send_instant_alert(ok, settings) is True
    assert should_send_instant_alert(low, settings) is False


def test_cluster_aggregator_picks_direction() -> None:
    rows = [
        {'direction': 'rial_weaker', 'weighted_score': 9.0, 'summary_fa': 'خبر 1'},
        {'direction': 'rial_weaker', 'weighted_score': 8.0, 'summary_fa': 'خبر 2'},
        {'direction': 'rial_stronger', 'weighted_score': 4.0, 'summary_fa': 'خبر 3'},
    ]
    totals = cluster_direction_scores(rows)
    direction = pick_cluster_alert(totals, min_score=16)
    assert direction == 'rial_weaker'
    top = top_cluster_rows(rows, 'rial_weaker', limit=2)
    assert len(top) == 2

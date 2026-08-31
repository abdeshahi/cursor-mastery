from __future__ import annotations

from collections import defaultdict
from typing import Literal

Direction = Literal['rial_weaker', 'rial_stronger', 'neutral']


def cluster_direction_scores(rows: list[dict]) -> dict[Direction, float]:
    totals: dict[Direction, float] = defaultdict(float)
    for row in rows:
        direction = row.get('direction', 'neutral')
        if direction not in ('rial_weaker', 'rial_stronger', 'neutral'):
            continue
        totals[direction] += float(row.get('weighted_score') or 0)
    return dict(totals)


def pick_cluster_alert(totals: dict[Direction, float], *, min_score: float) -> Direction | None:
    candidates = {
        direction: score
        for direction, score in totals.items()
        if direction != 'neutral' and score >= min_score
    }
    if not candidates:
        return None
    return max(candidates, key=candidates.get)


def top_cluster_rows(rows: list[dict], direction: Direction, limit: int = 3) -> list[dict]:
    filtered = [row for row in rows if row.get('direction') == direction]
    filtered.sort(key=lambda item: float(item.get('weighted_score') or 0), reverse=True)
    return filtered[:limit]

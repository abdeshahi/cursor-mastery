"""Deterministic event clustering without LLM."""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from app.core.config import Settings, get_settings
from app.models.news import NewsArticle, NewsEvent
from app.news.category import infer_category_hint
from app.news.normalization import jaccard_similarity, tokenize_for_similarity


@dataclass
class ClusterDecision:
    event: NewsEvent | None
    created: bool
    score: float = 0.0


class EventClusterer:
    """Conservative classical clustering for related articles."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        self._title_threshold = resolved.news_cluster_title_similarity_threshold
        self._token_threshold = resolved.news_cluster_token_similarity_threshold
        self._combined_threshold = resolved.news_cluster_combined_threshold
        self._default_window_hours = resolved.news_cluster_default_window_hours
        self._category_windows: dict[str, int] = {
            "MILITARY": resolved.news_cluster_military_window_hours,
            "SANCTIONS": resolved.news_cluster_sanctions_window_hours,
            "NEGOTIATION": resolved.news_cluster_negotiation_window_hours,
            "INFLATION": resolved.news_cluster_economic_window_hours,
            "MONETARY": resolved.news_cluster_economic_window_hours,
            "FX_POLICY": resolved.news_cluster_economic_window_hours,
            "OTHER": resolved.news_cluster_default_window_hours,
        }

    def _window_for_category(self, category_hint: str) -> timedelta:
        hours = self._category_windows.get(category_hint, self._default_window_hours)
        return timedelta(hours=hours)

    def _title_similarity(self, left: str, right: str) -> float:
        return SequenceMatcher(None, left, right).ratio()

    def _score_pair(self, article: NewsArticle, event: NewsEvent) -> float:
        title_sim = self._title_similarity(article.normalized_title, event.normalized_title)
        token_sim = jaccard_similarity(
            tokenize_for_similarity(article.title),
            tokenize_for_similarity(event.primary_title),
        )
        article_category = infer_category_hint(article.title, article.body)
        category_bonus = 0.1 if article_category == event.category_hint else -0.15
        return min(1.0, (0.6 * title_sim) + (0.4 * token_sim) + category_bonus)

    def _should_merge(self, article: NewsArticle, event: NewsEvent, score: float) -> bool:
        title_sim = self._title_similarity(article.normalized_title, event.normalized_title)
        token_sim = jaccard_similarity(
            tokenize_for_similarity(article.title),
            tokenize_for_similarity(event.primary_title),
        )
        article_category = infer_category_hint(article.title, article.body)
        if article_category != event.category_hint and title_sim < 0.92:
            return False
        if title_sim >= self._title_threshold:
            return True
        if score >= self._combined_threshold:
            return True
        if title_sim >= 0.70 and token_sim >= self._token_threshold and article_category == event.category_hint:
            return True
        return False

    def build_cluster_key(self, article: NewsArticle, category_hint: str) -> str:
        bucket = (article.published_at or article.received_at).strftime("%Y%m%d%H")
        digest = hashlib.sha256(f"{article.normalized_title}|{category_hint}|{bucket}".encode()).hexdigest()
        return digest[:32]

    def decide_cluster(
        self,
        article: NewsArticle,
        candidates: list[NewsEvent],
    ) -> ClusterDecision:
        category_hint = infer_category_hint(article.title, article.body)
        article_time = article.published_at or article.received_at
        window = self._window_for_category(category_hint)

        best: tuple[NewsEvent | None, float] = (None, 0.0)
        for event in candidates:
            if event.category_hint != category_hint and self._title_similarity(article.normalized_title, event.normalized_title) < 0.9:
                continue
            event_time = event.event_time or event.first_received_at
            if abs((article_time - event_time).total_seconds()) > window.total_seconds():
                continue
            score = self._score_pair(article, event)
            if score > best[1]:
                best = (event, score)

        if best[0] and self._should_merge(article, best[0], best[1]):
            return ClusterDecision(event=best[0], created=False, score=best[1])

        now = datetime.now(tz=article.received_at.tzinfo)
        new_event = NewsEvent(
            cluster_key=self.build_cluster_key(article, category_hint),
            primary_title=article.title,
            normalized_title=article.normalized_title,
            event_time=article.published_at or article.received_at,
            first_published_at=article.published_at,
            first_received_at=article.received_at,
            last_updated_at=now,
            language=article.language,
            source_count=0,
            article_count=0,
            category_hint=category_hint,
            status="active",
        )
        return ClusterDecision(event=new_event, created=True, score=0.0)

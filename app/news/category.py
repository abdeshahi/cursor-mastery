"""Deterministic non-LLM category hints from keywords."""

import re

from app.core.news_constants import NewsEventCategory

CATEGORY_KEYWORDS: dict[NewsEventCategory, tuple[str, ...]] = {
    NewsEventCategory.SANCTIONS: (
        "sanction",
        "تحریم",
        "ofac",
        "embargo",
    ),
    NewsEventCategory.NEGOTIATION: (
        "negotiat",
        "talks",
        "diplomacy",
        "مذاکره",
        "دیپلمات",
    ),
    NewsEventCategory.MILITARY: (
        "military",
        "strike",
        "missile",
        "نیروی نظامی",
        "موشک",
    ),
    NewsEventCategory.OIL_EXPORT: (
        "oil export",
        "brent",
        "opec",
        "نفت",
        "صادرات نفت",
    ),
    NewsEventCategory.FX_POLICY: (
        "exchange rate",
        "forex",
        "currency policy",
        "نرخ ارز",
        "سیاست ارزی",
    ),
    NewsEventCategory.MONETARY: (
        "central bank",
        "interest rate",
        "monetary",
        "بانک مرکزی",
        "نرخ بهره",
    ),
    NewsEventCategory.INFLATION: (
        "inflation",
        "cpi",
        "price index",
        "تورم",
    ),
    NewsEventCategory.FOREIGN_RESERVES: (
        "foreign reserve",
        "reserves",
        "ذخایر ارزی",
    ),
    NewsEventCategory.REGIONAL_RISK: (
        "regional",
        "middle east tension",
        "risk",
        "منطقه",
    ),
    NewsEventCategory.POLITICAL: (
        "parliament",
        "president",
        "government",
        "مجلس",
        "رئیس جمهور",
    ),
    NewsEventCategory.ECONOMIC: (
        "economy",
        "economic",
        "gdp",
        "اقتصاد",
    ),
}


def infer_category_hint(title: str, body: str | None = None) -> str:
    """Rule-based category hint for clustering/filtering only."""
    haystack = f"{title}\n{body or ''}".casefold()
    scores: dict[NewsEventCategory, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack or re.search(re.escape(keyword), haystack))
        if score:
            scores[category] = score
    if not scores:
        return NewsEventCategory.OTHER.value
    return max(scores, key=scores.get).value

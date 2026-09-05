"""Tests for news normalization utilities."""

from app.news.normalization import (
    canonicalize_url,
    compute_content_hash,
    jaccard_similarity,
    normalize_title,
    tokenize_for_similarity,
)


def test_normalize_title_strips_suffix_and_casefolds() -> None:
    assert normalize_title("Iran FX Policy - IRNA") == "iran fx policy"


def test_canonicalize_url_strips_tracking_params() -> None:
    raw = "https://Example.com/path/?utm_source=x&a=1"
    assert canonicalize_url(raw) == "https://example.com/path?a=1"


def test_compute_content_hash_is_stable() -> None:
    left = compute_content_hash("iran fx policy", "details")
    right = compute_content_hash("iran fx policy", "details")
    assert left == right
    assert len(left) == 64


def test_token_jaccard_similarity() -> None:
    left = tokenize_for_similarity("Iran central bank FX policy")
    right = tokenize_for_similarity("Central bank adjusts Iran FX policy")
    assert jaccard_similarity(left, right) > 0.3

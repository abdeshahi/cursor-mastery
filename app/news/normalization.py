"""Deterministic text, URL, and content normalization for news dedup/clustering."""

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Arabic/Persian character variants
ARABIC_YEH = "\u064A"
PERSIAN_YEH = "\u06CC"
ARABIC_KAF = "\u0643"
PERSIAN_KAF = "\u06A9"

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_eid", "ref")

SITE_SUFFIX_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\s*[-|–—]\s*خبرگزاری\s+.+$", re.IGNORECASE),
    re.compile(r"\s*[-|–—]\s*IRNA$", re.IGNORECASE),
    re.compile(r"\s*[-|–—]\s*BBC News$", re.IGNORECASE),
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_persian_characters(text: str) -> str:
    """Conservative Persian/Arabic character normalization for dedup only."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace(ARABIC_YEH, PERSIAN_YEH)
    normalized = normalized.replace(ARABIC_KAF, PERSIAN_KAF)
    normalized = normalized.translate(PERSIAN_DIGITS)
    normalized = normalized.translate(ARABIC_DIGITS)
    return normalized


def normalize_title(title: str, *, strip_suffixes: bool = True) -> str:
    """Deterministic title normalization; original title remains unchanged in DB."""
    text = normalize_persian_characters(title)
    text = normalize_whitespace(text)
    if strip_suffixes:
        for pattern in SITE_SUFFIX_PATTERNS:
            text = pattern.sub("", text)
    text = normalize_whitespace(text)
    return text.casefold()


def normalize_body_for_hash(body: str | None) -> str:
    if not body:
        return ""
    text = normalize_persian_characters(body)
    return normalize_whitespace(text)[:5000]


def compute_content_hash(normalized_title: str, body: str | None = None) -> str:
    payload = normalized_title + "\n" + normalize_body_for_hash(body)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonicalize_url(url: str) -> str:
    """Safe URL canonicalization preserving distinct content paths."""
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith(TRACKING_QUERY_PREFIXES) and key.lower() not in {"fbclid", "gclid", "ref"}
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((parsed.scheme.lower(), netloc, path, "", query, ""))


def tokenize_for_similarity(text: str) -> set[str]:
    normalized = normalize_persian_characters(text)
    tokens = re.findall(r"[\w\u0600-\u06FF]+", normalized.casefold())
    stopwords = {"the", "a", "an", "of", "in", "to", "and", "for", "on", "with", "از", "در", "به", "که", "این", "را"}
    return {token for token in tokens if len(token) > 2 and token not in stopwords}


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    union = len(left | right)
    return intersection / union if union else 0.0

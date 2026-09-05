"""News-related constants and default reliability scores."""

from enum import StrEnum


class NewsSourceType(StrEnum):
    OFFICIAL = "OFFICIAL"
    WIRE = "WIRE"
    MAJOR_MEDIA = "MAJOR_MEDIA"
    IRAN_FINANCIAL_MEDIA = "IRAN_FINANCIAL_MEDIA"
    VERIFIED_ANALYST = "VERIFIED_ANALYST"
    TELEGRAM = "TELEGRAM"
    SOCIAL = "SOCIAL"
    OTHER = "OTHER"


class NewsEventCategory(StrEnum):
    MILITARY = "MILITARY"
    SANCTIONS = "SANCTIONS"
    NEGOTIATION = "NEGOTIATION"
    OIL_EXPORT = "OIL_EXPORT"
    FX_POLICY = "FX_POLICY"
    MONETARY = "MONETARY"
    INFLATION = "INFLATION"
    FOREIGN_RESERVES = "FOREIGN_RESERVES"
    REGIONAL_RISK = "REGIONAL_RISK"
    POLITICAL = "POLITICAL"
    ECONOMIC = "ECONOMIC"
    OTHER = "OTHER"


class NewsEventStatus(StrEnum):
    ACTIVE = "active"
    MERGED = "merged"
    ARCHIVED = "archived"


# Default reliability by source type (configurable via DB; used for seeding only)
DEFAULT_RELIABILITY_BY_TYPE: dict[str, float] = {
    NewsSourceType.OFFICIAL.value: 1.00,
    NewsSourceType.WIRE.value: 0.95,
    NewsSourceType.MAJOR_MEDIA.value: 0.80,
    NewsSourceType.IRAN_FINANCIAL_MEDIA.value: 0.70,
    NewsSourceType.VERIFIED_ANALYST.value: 0.50,
    NewsSourceType.TELEGRAM.value: 0.20,
    NewsSourceType.SOCIAL.value: 0.10,
    NewsSourceType.OTHER.value: 0.50,
}

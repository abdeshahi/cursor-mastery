"""Market unit conversion and documentation.

Internal storage standards (all prices persisted in these units):
- USD_IRR: Iranian Rial (IRR) per 1 USD
- USDT_IRR: Iranian Rial (IRR) per 1 USDT
- AED_IRR: Iranian Rial (IRR) per 1 AED
- GOLD_18K_IRR: Iranian Rial (IRR) per 1 gram of 18-karat gold (TGJU geram18 unit)
- GOLD_OUNCE_USD: US Dollars (USD) per 1 troy ounce of gold
- BRENT_USD: US Dollars (USD) per 1 barrel of Brent crude
- USD_BROAD_INDEX: FRED broad trade-weighted USD index (unitless index value)

Iranian exchange quote conversion:
- 1 TOMAN = 10 IRR (explicit, tested, never assumed silently)
"""

from decimal import Decimal

TOMAN_TO_IRR: Decimal = Decimal("10")


def toman_to_irr(amount: Decimal) -> Decimal:
    """Convert an Iranian Toman-denominated amount to Rial."""
    return amount * TOMAN_TO_IRR


def parse_decimal(value: str | int | float) -> Decimal:
    """Parse numeric strings that may contain thousands separators."""
    if isinstance(value, Decimal):
        return value
    cleaned = str(value).replace(",", "").strip()
    if not cleaned:
        raise ValueError("empty numeric value")
    return Decimal(cleaned)

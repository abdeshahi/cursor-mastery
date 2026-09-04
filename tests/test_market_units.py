"""Tests for market unit conversion."""

from decimal import Decimal

import pytest

from app.providers.market.units import TOMAN_TO_IRR, parse_decimal, toman_to_irr


def test_toman_to_irr_conversion() -> None:
    assert toman_to_irr(Decimal("220229")) == Decimal("2202290")
    assert TOMAN_TO_IRR == Decimal("10")


def test_parse_decimal_with_commas() -> None:
    assert parse_decimal("2,214,200") == Decimal("2214200")


def test_parse_decimal_rejects_empty() -> None:
    with pytest.raises(ValueError):
        parse_decimal("")

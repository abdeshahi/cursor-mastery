from datetime import datetime

from app.services.persian_utils import format_jalali_date_persian, format_amount_persian, to_persian_digits


def test_to_persian_digits() -> None:
    assert to_persian_digits('123') == '۱۲۳'
    assert to_persian_digits('1404/06/12') == '۱۴۰۴/۰۶/۱۲'


def test_format_amount_persian() -> None:
    assert format_amount_persian(1300000) == '۱,۳۰۰,۰۰۰'


def test_format_jalali_date_persian_has_persian_digits() -> None:
    value = format_jalali_date_persian(datetime(2026, 9, 2, 12, 0))
    assert all(ch in '۰۱۲۳۴۵۶۷۸۹/' for ch in value if not ch.isascii() or ch == '/')
    assert '۱۴' in value or '۱۵' in value

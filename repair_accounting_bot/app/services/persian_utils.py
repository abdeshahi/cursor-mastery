from __future__ import annotations

from datetime import datetime

import jdatetime

PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'


def to_persian_digits(value: str | int) -> str:
    return ''.join(PERSIAN_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def format_jalali_date_persian(when: datetime | None = None) -> str:
    when = when or datetime.now()
    jalali = jdatetime.datetime.fromgregorian(datetime=when)
    raw = f'{jalali.year}/{jalali.month:02d}/{jalali.day:02d}'
    return to_persian_digits(raw)


def format_amount_persian(amount: int) -> str:
    return to_persian_digits(f'{amount:,}')

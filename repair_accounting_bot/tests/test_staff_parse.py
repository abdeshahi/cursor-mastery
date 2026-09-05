from app.bot.parsing import parse_staff_args


def test_parse_staff_args_id_first() -> None:
    assert parse_staff_args('5123456789|نهال') == (5123456789, 'نهال')


def test_parse_staff_args_name_first() -> None:
    assert parse_staff_args('نهال|5123456789') == (5123456789, 'نهال')


def test_parse_staff_args_invalid() -> None:
    assert parse_staff_args('نهال|علی') is None
    assert parse_staff_args('نهال') is None

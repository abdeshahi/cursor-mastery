from app.bot.invite_utils import build_invite_link, extract_invite_token, new_invite_token


def test_new_invite_token_format() -> None:
    token = new_invite_token()
    assert token.startswith('inv_')
    assert len(token) > 10


def test_extract_invite_token() -> None:
    assert extract_invite_token('/start inv_abc123') == 'inv_abc123'
    assert extract_invite_token('/start@cttelfixbot inv_abc123') == 'inv_abc123'
    assert extract_invite_token('/start') is None
    assert extract_invite_token('hello') is None


def test_build_invite_link() -> None:
    link = build_invite_link('cttelfixbot', 'inv_deadbeef')
    assert link == 'https://t.me/cttelfixbot?start=inv_deadbeef'

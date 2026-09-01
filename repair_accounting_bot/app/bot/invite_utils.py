from __future__ import annotations

import secrets

INVITE_PREFIX = 'inv_'


def extract_invite_token(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return None
    command = parts[0].split('@')[0].lower()
    if command != '/start' or len(parts) < 2:
        return None
    token = parts[1].strip()
    if token.startswith(INVITE_PREFIX) and len(token) > len(INVITE_PREFIX):
        return token
    return None


def build_invite_link(bot_username: str, token: str) -> str:
    username = bot_username.lstrip('@')
    return f'https://t.me/{username}?start={token}'


def new_invite_token() -> str:
    return f'{INVITE_PREFIX}{secrets.token_hex(8)}'

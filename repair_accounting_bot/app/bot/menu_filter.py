from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.ui.themes import Theme, get_theme


class MenuFilter(BaseFilter):
    def __init__(self, key: str) -> None:
        self.key = key

    async def __call__(self, message: Message, theme: Theme | None = None) -> bool:
        if not isinstance(message, Message) or not message.text:
            return False
        active = theme or get_theme(None)
        return message.text.strip() == active.label(self.key)

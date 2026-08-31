from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='/status'), KeyboardButton(text='/digest')],
        [KeyboardButton(text='/on'), KeyboardButton(text='/off')],
        [KeyboardButton(text='/sources'), KeyboardButton(text='/help')],
    ],
    resize_keyboard=True,
)

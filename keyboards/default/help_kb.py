"""Reply keyboard for the /help command."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_help_keyboard() -> ReplyKeyboardMarkup:
    """Return a simple reply keyboard shown on /help."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="/start"),
        KeyboardButton(text="/help"),
    )
    return builder.as_markup(resize_keyboard=True)

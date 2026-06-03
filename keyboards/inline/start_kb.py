"""Inline keyboard for the /start command with optional premium icon."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Custom emoji ID shown as a button icon.
# Requires the bot owner to have Telegram Premium; ignored silently otherwise.
ICON_STAR = "5453969572354878595"


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Return the /start inline keyboard demonstrating icon_custom_emoji_id.

    Left button has icon_custom_emoji_id set (requires bot owner Telegram Premium).
    Right button has no icon — shown as a plain button in all cases.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Premium user (icon enabled)",
                callback_data="demo_premium",
                icon_custom_emoji_id=ICON_STAR,
            ),
            InlineKeyboardButton(
                text="Regular user (no icon)",
                callback_data="demo_regular",
            ),
        ]]
    )

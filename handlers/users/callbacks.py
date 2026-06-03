"""Handles inline button callbacks from the /start demo keyboard."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="users:callbacks")


@router.callback_query(F.data == "demo_premium")
async def demo_premium_callback(callback: CallbackQuery) -> None:
    await callback.answer(
        "⭐ This button uses icon_custom_emoji_id — "
        "the icon is visible when the bot owner has Telegram Premium.",
        show_alert=True,
    )


@router.callback_query(F.data == "demo_regular")
async def demo_regular_callback(callback: CallbackQuery) -> None:
    await callback.answer(
        "A regular button without a custom icon.",
        show_alert=True,
    )

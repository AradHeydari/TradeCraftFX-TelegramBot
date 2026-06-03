"""Handles the /help command."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.default import get_help_keyboard

router = Router(name="users:help")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "<b>Available commands:</b>\n"
        "/start — start the bot and see an inline keyboard example\n"
        "/help — show this message\n\n"
        "Any text you send will be echoed back.\n"
        "Try /start to see inline buttons with premium icon support.",
        reply_markup=get_help_keyboard(),
    )

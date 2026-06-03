"""Handles the /start command."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.inline import get_start_keyboard

router = Router(name="users:start")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    name = message.from_user.full_name if message.from_user else "friend"
    await message.answer(
        f'<tg-emoji emoji-id="5453969572354878595">⭐</tg-emoji> Hello, <b>{name}</b>! 👋\n'
        "I'm an aiogram 3 starter template bot.\n\n"
        "<b>Icon custom emoji test</b>\n\n"
        "Left button: <code>icon_custom_emoji_id</code> set\n"
        "Right button: no icon\n\n"
        "If you have Telegram Premium (as bot owner), the left button shows a star icon.",
        reply_markup=get_start_keyboard(),
    )

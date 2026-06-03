"""Notify admins when the bot starts or stops."""
from __future__ import annotations

import logging

from aiogram import Bot

from data.config import settings

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    logger.info("Bot started")
    for admin_id in settings.admins:
        try:
            await bot.send_message(admin_id, "✅ Bot started")
        except Exception as error:  # noqa: BLE001
            logger.warning("Could not notify admin %s: %s", admin_id, error)


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot stopped")
    for admin_id in settings.admins:
        try:
            await bot.send_message(admin_id, "⛔️ Bot stopped")
        except Exception:  # noqa: BLE001
            pass

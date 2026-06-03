"""Bot entry point."""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram.types import BotCommandScopeAllPrivateChats

from handlers import setup_routers
from loader import bot, dp
from middlewares.logging import LoggingMiddleware
from utils.notify_admins import on_shutdown, on_startup
from utils.set_botcommands import commands


async def main() -> None:
    dp.message.middleware(LoggingMiddleware())
    dp.include_router(setup_routers())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())

"""Bot command menu entries."""
from __future__ import annotations

from aiogram.types import BotCommand

commands = [
    BotCommand(command="start", description="Start the bot"),
    BotCommand(command="help", description="Help"),
]

"""Assembles Bot, Dispatcher, and FSM storage (Memory or Redis)."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from data.config import settings


def get_storage() -> BaseStorage:
    """Return RedisStorage if USE_REDIS=true, otherwise MemoryStorage."""
    if settings.use_redis:
        return RedisStorage.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/0"
        )
    return MemoryStorage()


bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=get_storage())

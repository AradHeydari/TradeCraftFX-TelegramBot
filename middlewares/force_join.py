from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

class ForceJoinMiddleware(BaseMiddleware):
    """
    میان‌افزار بررسی عضویت اجباری در کانال
    (فعلاً غیرفعال است)
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # این میان‌افزار فعلاً غیرفعال است
        # برای فعال‌سازی، کدهای بررسی عضویت را اضافه کنید
        return await handler(event, data)
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import Config
from database.db import init_db
from handlers import user_handlers, admin_handlers, support_handlers
from services.scheduler import setup_scheduler

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)

bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

async def on_startup():
    await init_db()
    setup_scheduler(bot)
    print("✅ دیتابیس راه‌اندازی شد.")
    print("⏰ زمان‌بند راه‌اندازی شد.")
    print("🚀 ربات با موفقیت راه‌اندازی شد!")

async def main():
    dp.startup.register(on_startup)
    
    # ثبت همه هندلرها
    dp.include_router(user_handlers.router)      # اول: دستورات کاربر
    dp.include_router(support_handlers.router)   # دوم: تیکت‌ها (با FSM)
    dp.include_router(admin_handlers.router)     # آخر: مدیریت (broadcast)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ ربات متوقف شد.")
import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from config import Config
from database.db import init_db
from services.scheduler import setup_scheduler
from middlewares.force_join import ForceJoinMiddleware
from handlers import user_handlers, admin_handlers

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)

# ایجاد ربات
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# ایجاد دیسپچر
dp = Dispatcher()

async def on_startup():
    """کارهایی که هنگام شروع ربات انجام می‌شود"""
    # راه‌اندازی دیتابیس
    await init_db()
    print("✅ دیتابیس راه‌اندازی شد.")
    
    # راه‌اندازی زمان‌بند
    setup_scheduler()
    print("✅ زمان‌بند راه‌اندازی شد.")

async def on_shutdown():
    """کارهایی که هنگام توقف ربات انجام می‌شود"""
    print("⛔ ربات در حال توقف...")

async def main():
    """تابع اصلی اجرای ربات"""
    
    # ثبت رویدادهای شروع و توقف
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # ثبت میان‌افزارها (عضویت اجباری - اختیاری)
    # dp.message.middleware(ForceJoinMiddleware())
    # dp.callback_query.middleware(ForceJoinMiddleware())
    
    # ثبت هندلرها
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    
    
    # حذف webhook
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 ربات Trade Craft FX با موفقیت ساخته شد!")
    
    # شروع دریافت پیام‌ها
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ ربات توسط کاربر متوقف شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")
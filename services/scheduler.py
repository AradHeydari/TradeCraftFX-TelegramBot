from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

scheduler = AsyncIOScheduler()

async def check_expired_subscriptions():
    print("🔄 بررسی اشتراک‌های منقضی‌شده...")
    # کد بررسی اینجا قرار می‌گیرد

async def send_expiry_reminders():
    print("🔄 ارسال یادآوری...")

def setup_scheduler():
    scheduler.add_job(
        check_expired_subscriptions,
        CronTrigger(hour=0, minute=0),
        id="check_expired",
        replace_existing=True
    )
    scheduler.add_job(
        send_expiry_reminders,
        CronTrigger(hour=9, minute=0),
        id="send_reminders",
        replace_existing=True
    )
    scheduler.start()
    print("⏰ زمان‌بند راه‌اندازی شد.")
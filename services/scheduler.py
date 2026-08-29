from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

scheduler = AsyncIOScheduler()

async def check_expired_subscriptions(bot):
    """بررسی اشتراک‌های منقضی‌شده و غیرفعال کردن + کیک از کانال"""
    print("🔄 در حال بررسی اشتراک‌های منقضی‌شده...")
    
    expired_users = await get_expired_users()
    
    for user in expired_users:
        # غیرفعال کردن اشتراک در دیتابیس
        await update_user_subscription(
            user_id=user["user_id"],
            plan=user["plan"],
            start_date=user["subscription_start"],
            end_date=user["subscription_end"],
            active=False
        )
        print(f"❌ کاربر {user['user_id']} غیرفعال شد.")
        
        # ✅ کیک کردن کاربر از کانال
        try:
            await bot.ban_chat_member(
                chat_id=Config.CHANNEL_ID,
                user_id=user["user_id"]
            )
            # برای اینکه کاربر بتواند دوباره با خرید مجدد عضو شود، انبن می‌کنیم
            await bot.unban_chat_member(
                chat_id=Config.CHANNEL_ID,
                user_id=user["user_id"]
            )
            print(f"🚫 کاربر {user['user_id']} از کانال کیک شد.")
        except Exception as e:
            print(f"خطا در کیک کردن کاربر {user['user_id']}: {e}")
    
    print(f"✅ {len(expired_users)} کاربر غیرفعال و از کانال کیک شدند.")

async def send_expiry_reminders():
    print("🔄 ارسال یادآوری...")

def setup_scheduler(bot):
    """راه‌اندازی زمان‌بند با دریافت bot"""
    # بررسی انقضا هر شب ساعت ۰۰:۰۰ (با کیک کردن)
    scheduler.add_job(
        check_expired_subscriptions,
        CronTrigger(hour=0, minute=0),
        args=[bot],  # ✅ ارسال bot به تابع
        id="check_expired",
        replace_existing=True
    )
    
    # یادآوری هر روز ساعت ۰۹:۰۰ (همان قابلیت قبلی)
    scheduler.add_job(
        send_expiry_reminders,
        CronTrigger(hour=9, minute=0),
        id="send_reminders",
        replace_existing=True
    )
    
    scheduler.start()
    print("⏰ زمان‌بند وظایف راه‌اندازی شد.")
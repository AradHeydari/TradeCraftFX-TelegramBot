import aiosqlite
from typing import AsyncGenerator
from config import Config

DATABASE_URL = Config.DATABASE_URL

async def init_db():
    """ایجاد تمام جداول در صورت عدم وجود"""
    import os
    # اطمینان از وجود پوشه data
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_URL) as db:
        # جدول کاربران
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscription_start TEXT,
                subscription_end TEXT,
                plan TEXT,
                is_active INTEGER DEFAULT 0,
                registered_at TEXT
            )
        """)
        
        # جدول تراکنش‌ها
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                plan TEXT,
                payment_method TEXT,
                payment_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                confirmed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # جدول تیکت‌ها
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT,
                answer TEXT,
                answered_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # جدول کدهای تخفیف
        await db.execute("""
            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                discount_percent INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        #جدول قیمت ها
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        # جدول تنظیمات (برای ذخیره قیمت‌ها)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
            )
        """)
        
        await db.commit()

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """ارائه اتصال دیتابیس به هندلرها"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        yield db
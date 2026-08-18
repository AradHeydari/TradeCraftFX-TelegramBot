import aiosqlite
from datetime import datetime, timedelta
from typing import List, Optional
from .db import DATABASE_URL
from config import Config

# ==================== کاربران ====================

async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def create_user(user_id: int, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, first_name, datetime.now().isoformat())
        )
        await db.commit()

async def update_user_subscription(
    user_id: int, plan: str, start_date: str, end_date: str, active: bool = True
):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            UPDATE users 
            SET plan = ?, subscription_start = ?, subscription_end = ?, is_active = ?
            WHERE user_id = ?
            """,
            (plan, start_date, end_date, 1 if active else 0, user_id)
        )
        await db.commit()

async def get_all_active_users() -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE is_active = 1")
        return await cursor.fetchall()

async def get_expired_users() -> List[dict]:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE is_active = 1 AND subscription_end < ?",
            (now,)
        )
        return await cursor.fetchall()

async def get_all_users() -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users")
        return await cursor.fetchall()

async def get_expiring_soon_users(days: int = 7) -> List[dict]:
    """دریافت کاربرانی که اشتراکشان تا روزهای مشخص منقضی می‌شود"""
    from datetime import datetime, timedelta
    now = datetime.now()
    future = (now + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM users 
            WHERE is_active = 1 
            AND subscription_end > ? 
            AND subscription_end <= ?
            """,
            (now.isoformat(), future)
        )
        return await cursor.fetchall()

async def get_new_users_since(date: str) -> List[dict]:
    """دریافت کاربرانی که بعد از تاریخ مشخص ثبت‌نام کرده‌اند"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE registered_at >= ?",
            (date,)
        )
        return await cursor.fetchall()

# ==================== تراکنش‌ها ====================

async def create_transaction(
    user_id: int, amount: int, plan: str, payment_method: str, payment_id: str
):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT INTO transactions 
            (user_id, amount, plan, payment_method, payment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, amount, plan, payment_method, payment_id, datetime.now().isoformat())
        )
        await db.commit()

async def update_transaction_status(payment_id: str, status: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            UPDATE transactions 
            SET status = ?, confirmed_at = ? 
            WHERE payment_id = ?
            """,
            (status, datetime.now().isoformat() if status == "paid" else None, payment_id)
        )
        await db.commit()

async def get_all_transactions(limit: int = 100) -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return await cursor.fetchall()

async def get_monthly_income(year: int, month: int) -> int:
    start_date = datetime(year, month, 1).isoformat()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).isoformat()
    else:
        end_date = datetime(year, month + 1, 1).isoformat()
    
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            """
            SELECT SUM(amount) as total 
            FROM transactions 
            WHERE status = 'paid' 
            AND created_at >= ? AND created_at < ?
            """,
            (start_date, end_date)
        )
        row = await cursor.fetchone()
        return row[0] if row[0] else 0

async def get_transactions_by_user(user_id: int) -> List[dict]:
    """دریافت لیست تراکنش‌های یک کاربر"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_transaction(payment_id: str) -> Optional[dict]:
    """دریافت اطلاعات یک تراکنش بر اساس شناسه پرداخت"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE payment_id = ?",
            (payment_id,)
        )
        return await cursor.fetchone()


# ==================== تخفیف‌ها ====================

async def create_discount(code: str, percent: int, max_uses: int, expires_at: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT INTO discounts (code, discount_percent, max_uses, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (code, percent, max_uses, expires_at)
        )
        await db.commit()

async def get_discount(code: str) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM discounts WHERE code = ? AND is_active = 1",
            (code,)
        )
        return await cursor.fetchone()

async def get_all_discounts() -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM discounts ORDER BY id DESC")
        return await cursor.fetchall()

async def use_discount(code: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE discounts SET used_count = used_count + 1 WHERE code = ?",
            (code,)
        )
        await db.commit()
        # اگر به حداکثر رسید، غیرفعال کن
        discount = await get_discount(code)
        if discount and discount["used_count"] >= discount["max_uses"]:
            await db.execute(
                "UPDATE discounts SET is_active = 0 WHERE code = ?",
                (code,)
            )
            await db.commit()

# ==================== پخش همگانی ====================

async def create_broadcast(message: str) -> int:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            """
            INSERT INTO broadcasts (message, created_at)
            VALUES (?, ?)
            """,
            (message, datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid

async def update_broadcast_stats(broadcast_id: int, sent: int, failed: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            UPDATE broadcasts 
            SET sent_count = sent_count + ?, failed_count = failed_count + ?
            WHERE id = ?
            """,
            (sent, failed, broadcast_id)
        )
        await db.commit()

# ==================== تیکت‌ها ====================

async def create_ticket(user_id: int, subject: str, message: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT INTO tickets (user_id, subject, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, subject, message, datetime.now().isoformat())
        )
        await db.commit()

async def get_ticket(ticket_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        return await cursor.fetchone()

async def get_user_tickets(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_all_tickets() -> List[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC"
        )
        return await cursor.fetchall()

async def answer_ticket(ticket_id: int, answer: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            UPDATE tickets 
            SET answer = ?, status = 'answered', answered_at = ?
            WHERE id = ?
            """,
            (answer, datetime.now().isoformat(), ticket_id)
        )
        await db.commit()

async def close_ticket(ticket_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = ?",
            (ticket_id,)
        )
        await db.commit()


# ==================== تنظیمات (قیمت‌ها) ====================

async def get_price(plan_key: str) -> int:
    """دریافت قیمت یک پلن از دیتابیس"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?",
            (f"price_{plan_key}",)
        )
        row = await cursor.fetchone()
        if row:
            return int(row[0])
        # اگر در دیتابیس نبود، از مقدار پیش‌فرض Config استفاده کن
        return Config.PRICES.get(plan_key, 0)

async def set_price(plan_key: str, price: int):
    """ذخیره قیمت یک پلن در دیتابیس"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
            """,
            (f"price_{plan_key}", str(price))
        )
        await db.commit()
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Optional
from .db import DATABASE_URL

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
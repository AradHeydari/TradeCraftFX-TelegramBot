import aiosqlite
import asyncio

async def check_settings():
    try:
        async with aiosqlite.connect("data/iran_crypto.db") as db:
            cursor = await db.execute("SELECT * FROM settings")
            rows = await cursor.fetchall()
            if rows:
                print("✅ داده‌های موجود در جدول settings:")
                for row in rows:
                    print(f"   {row[0]} = {row[1]}")
            else:
                print("❌ جدول settings خالی است یا وجود ندارد.")
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")

if __name__ == "__main__":
    asyncio.run(check_settings())
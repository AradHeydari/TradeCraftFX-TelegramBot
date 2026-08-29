import asyncio
from database.repository import get_price

async def test():
    price_1m = await get_price("1m")
    price_12m = await get_price("12m")
    print(f"price_1m = {price_1m}")
    print(f"price_12m = {price_12m}")

if __name__ == "__main__":
    asyncio.run(test())
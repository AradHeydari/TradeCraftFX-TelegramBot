import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """تنظیمات اصلی ربات"""
    
    # توکن و ادمین‌ها
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
    
    # کانال‌ها
    PRIVATE_CHANNEL_LINK = os.getenv("PRIVATE_CHANNEL_LINK", "")
    PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", "")
    
    # اطلاعات بانکی
    CARD_NUMBER = os.getenv("CARD_NUMBER", "6037999999999999")
    CARD_OWNER = os.getenv("CARD_OWNER", "علی رضایی")
    
    # ارز دیجیتال
    CRYPTO_TYPE = os.getenv("CRYPTO_TYPE", "USDT")
    CRYPTO_NETWORK = os.getenv("CRYPTO_NETWORK", "TRC20")
    CRYPTO_WALLET = os.getenv("CRYPTO_WALLET", "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    # پشتیبانی
    SUPPORT_IDS = [
        os.getenv("SUPPORT_ID_1", "@support1"),
        os.getenv("SUPPORT_ID_2", "@support2"),
        os.getenv("SUPPORT_ID_3", "@support3"),
    ]
    
    # قیمت‌های پیش‌فرض
    PRICES = {
        "1m": int(os.getenv("DEFAULT_PRICE_1M", 40)),
        "3m": int(os.getenv("DEFAULT_PRICE_3M", 80)),
        "6m": int(os.getenv("DEFAULT_PRICE_6M", 120)),
        "12m": int(os.getenv("DEFAULT_PRICE_12M", 230)),
    }
    
    # اطلاعات پلن‌ها
    PLANS = {
        "1m": {"name": "یک ماهه", "months": 1},
        "3m": {"name": "سه ماهه", "months": 3},
        "6m": {"name": "شش ماهه", "months": 6},
        "12m": {"name": "یک ساله", "months": 12},
    }
    
    # تنظیمات دیتابیس
    DATABASE_URL = "data/iran_crypto.db"
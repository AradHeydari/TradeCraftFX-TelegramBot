from config import Config

async def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین است یا خیر"""
    return user_id in Config.ADMINS

def validate_iran_card_number(card_number: str) -> bool:
    """اعتبارسنجی شماره کارت بانکی ایران (ساده)"""
    if not card_number.isdigit() or len(card_number) != 16:
        return False
    # الگوریتم Luhn
    total = 0
    for i, digit in enumerate(reversed(card_number)):
        n = int(digit) * (2 if i % 2 == 1 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0

def validate_crypto_address(address: str) -> bool:
    """اعتبارسنجی آدرس ارز دیجیتال (ساده)"""
    # فقط برای تست - در عمل باید اعتبارسنجی کامل‌تری انجام داد
    return len(address) >= 10 and address.isalnum()
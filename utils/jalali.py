import jdatetime
from datetime import datetime

def to_jalali(gregorian_date: datetime) -> str:
    """تبدیل تاریخ میلادی به شمسی با فرمت YYYY/MM/DD"""
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)
    return jalali_date.strftime("%Y/%m/%d")

def to_jalali_full(gregorian_date: datetime) -> str:
    """تبدیل تاریخ میلادی به شمسی کامل با نام ماه و روز هفته"""
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)
    return jalali_date.strftime("%A, %d %B %Y")

def get_jalali_month_name(gregorian_date: datetime) -> str:
    """دریافت نام ماه شمسی"""
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)
    return jalali_date.strftime("%B %Y")

def get_remaining_days(end_date: datetime) -> int:
    """محاسبه روزهای باقی‌مانده تا تاریخ انقضا"""
    remaining = (end_date - datetime.now()).days
    return max(0, remaining)

def now_jalali() -> str:
    """دریافت تاریخ و زمان فعلی به شمسی"""
    return jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M")

def today_jalali() -> str:
    """دریافت تاریخ امروز به شمسی"""
    return jdatetime.date.today().strftime("%Y/%m/%d")
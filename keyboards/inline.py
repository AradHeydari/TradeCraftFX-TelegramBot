from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config


def get_main_keyboard():
    """منوی اصلی با ۸ گزینه (افزودن گزینه تیکت)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید اشتراک", callback_data="buy")],
            [InlineKeyboardButton(text="💳 تمدید اشتراک", callback_data="renew")],
            [InlineKeyboardButton(text="👤 حساب کاربری", callback_data="profile")],
            [InlineKeyboardButton(text="📊 وضعیت اشتراک", callback_data="status")],
            [InlineKeyboardButton(text="📞 پشتیبانی", callback_data="support")],
            [InlineKeyboardButton(text="📚 آموزش استفاده", callback_data="help")],
            [InlineKeyboardButton(text="🎁 کد تخفیف", callback_data="discount")],
            [InlineKeyboardButton(text="🎫 ثبت تیکت", callback_data="new_ticket")],  # ✅ گزینه جدید
        ]
    )

def get_plans_keyboard(prices: dict):
    """دکمه‌های انتخاب پلن با قیمت‌های دریافتی از دیتابیس"""
    buttons = []
    for key, plan in Config.PLANS.items():
        price = prices.get(key, 0)
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {plan['name']} - {price}$",
                callback_data=f"plan_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_methods_keyboard():
    """روش‌های پرداخت"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 کارت به کارت", callback_data="payment_card")],
            [InlineKeyboardButton(text="🌐 درگاه پرداخت", callback_data="payment_gateway")],
            [InlineKeyboardButton(text="🪙 ارز دیجیتال", callback_data="payment_crypto")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")],
        ]
    )

def get_confirm_payment_keyboard(payment_id: str):
    """تأیید پرداخت (برای کاربر)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ پرداخت انجام شد", callback_data=f"confirm_{payment_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")],
        ]
    )

def get_admin_panel_keyboard():
    """پنل مدیریت"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار کلی", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 لیست تراکنش‌ها", callback_data="admin_transactions")],
            [InlineKeyboardButton(text="🎁 مدیریت تخفیف‌ها", callback_data="admin_discounts")],
            [InlineKeyboardButton(text="📨 ارسال پیام همگانی", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📞 مدیریت تیکت‌ها", callback_data="admin_tickets")],
            [InlineKeyboardButton(text="🔧 تغییر قیمت‌ها", callback_data="admin_prices")],
            [InlineKeyboardButton(text="📈 گزارش فروش", callback_data="admin_sales_report")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")],
        ]
    )

def get_admin_user_actions_keyboard(user_id: int):
    """عملیات مدیریتی روی یک کاربر"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 تمدید اشتراک", callback_data=f"admin_renew_{user_id}")],
            [InlineKeyboardButton(text="❌ غیرفعال کردن", callback_data=f"admin_deactivate_{user_id}")],
            [InlineKeyboardButton(text="📋 تاریخچه تراکنش", callback_data=f"admin_user_trans_{user_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_users")],
        ]
    )

def get_ticket_action_keyboard(ticket_id: int):
    """عملیات روی تیکت"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ پاسخ به تیکت", callback_data=f"ticket_answer_{ticket_id}")],
            [InlineKeyboardButton(text="❌ بستن تیکت", callback_data=f"ticket_close_{ticket_id}")],
        ]
    )

def get_back_keyboard():
    """فقط دکمه بازگشت"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")]
        ]
    )



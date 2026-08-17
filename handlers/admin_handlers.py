from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.repository import (
    get_all_users, get_all_active_users, get_all_transactions,
    get_monthly_income, get_user, get_expired_users,
    update_transaction_status, update_user_subscription
)
from keyboards.inline import get_admin_panel_keyboard
from utils.jalali import get_jalali_month_name
from utils.helpers import is_admin

router = Router()

# ==================== ورود به پنل ====================

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return
    
    await message.answer(
        "👑 **پنل مدیریت**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )

# ==================== آمار کلی ====================

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    users = await get_all_users()
    active_users = await get_all_active_users()
    expired_users = await get_expired_users()
    
    income = await get_monthly_income(datetime.now().year, datetime.now().month)
    
    text = (
        f"📊 **آمار کلی ربات**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 کل کاربران: {len(users)}\n"
        f"✅ کاربران فعال: {len(active_users)}\n"
        f"❌ کاربران منقضی: {len(expired_users)}\n"
        f"💰 درآمد این ماه: {income:,} دلار\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📅 {get_jalali_month_name(datetime.now())}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== لیست تراکنش‌ها با دکمه تأیید و رد ====================

@router.callback_query(lambda c: c.data == "admin_transactions")
async def admin_transactions(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    transactions = await get_all_transactions(50)
    
    if not transactions:
        await callback.message.edit_text("📭 **هیچ تراکنشی یافت نشد.**")
        await callback.answer()
        return
    
    text = "💰 **لیست تراکنش‌ها**\n━━━━━━━━━━━━━━━━━\n"
    buttons = []
    
    for t in transactions:
        status_icon = "✅" if t["status"] == "paid" else "⏳" if t["status"] == "pending" else "❌"
        text += f"{status_icon} ID:{t['payment_id']} - {t['amount']}$ - {t['plan']}\n"
        
        # اگر تراکنش در حالت انتظار است، دکمه تأیید و رد اضافه کن
        if t["status"] == "pending":
            buttons.append([
                InlineKeyboardButton(
                    text=f"✅ تأیید {t['payment_id']}",
                    callback_data=f"admin_confirm_{t['payment_id']}"
                ),
                InlineKeyboardButton(
                    text=f"❌ رد {t['payment_id']}",
                    callback_data=f"admin_reject_{t['payment_id']}"
                )
            ])
    
    text += f"\n📊 کل: {len(transactions)} تراکنش"
    
    # دکمه بازگشت به پنل
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_admin")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== تأیید پرداخت ====================

@router.callback_query(lambda c: c.data.startswith("admin_confirm_"))
async def admin_confirm_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    payment_id = callback.data.replace("admin_confirm_", "")
    
    # به‌روزرسانی وضعیت تراکنش به paid
    await update_transaction_status(payment_id, "paid")
    
    # دریافت اطلاعات تراکنش برای اطلاع‌رسانی به کاربر
    from database.repository import get_transaction
    transaction = await get_transaction(payment_id)
    
    if transaction:
        user_id = transaction["user_id"]
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ **پرداخت شما با موفقیت تأیید شد!**\n\n"
                    f"📌 شناسه پرداخت: `{payment_id}`\n"
                    f"💰 مبلغ: {transaction['amount']} دلار\n"
                    f"📅 پلن: {Config.PLANS[transaction['plan']]['name']}\n\n"
                    f"🎉 اشتراک شما فعال شد. از خدمات ما لذت ببرید!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    
    await callback.message.edit_text(
        f"✅ **پرداخت با شناسه `{payment_id}` تأیید شد.**\n\n"
        f"به کاربر اطلاع‌رسانی شد.",
        parse_mode="Markdown"
    )
    await callback.answer("✅ پرداخت تأیید شد!")

# ==================== رد پرداخت ====================

@router.callback_query(lambda c: c.data.startswith("admin_reject_"))
async def admin_reject_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    payment_id = callback.data.replace("admin_reject_", "")
    
    # به‌روزرسانی وضعیت تراکنش به failed
    await update_transaction_status(payment_id, "failed")
    
    # اطلاع‌رسانی به کاربر
    from database.repository import get_transaction
    transaction = await get_transaction(payment_id)
    
    if transaction:
        user_id = transaction["user_id"]
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ **پرداخت شما رد شد.**\n\n"
                    f"📌 شناسه پرداخت: `{payment_id}`\n\n"
                    f"در صورت نیاز با پشتیبانی تماس بگیرید."
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    
    await callback.message.edit_text(
        f"❌ **پرداخت با شناسه `{payment_id}` رد شد.**\n\n"
        f"به کاربر اطلاع‌رسانی شد.",
        parse_mode="Markdown"
    )
    await callback.answer("❌ پرداخت رد شد!")

# ==================== بازگشت به پنل ====================

@router.callback_query(lambda c: c.data == "back_admin")
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👑 **پنل مدیریت**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
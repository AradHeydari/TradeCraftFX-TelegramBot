import uuid
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from config import Config
from database.repository import (
    get_user, create_user, get_transactions_by_user,
    create_transaction
)
from keyboards.inline import (
    get_main_keyboard, get_plans_keyboard,
    get_payment_methods_keyboard, get_confirm_payment_keyboard,
    get_back_keyboard
)
from utils.jalali import to_jalali_full, get_remaining_days

router = Router()

# ==================== دستور /start ====================

@router.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    await create_user(user.id, user.username, user.first_name)
    
    db_user = await get_user(user.id)
    
    if db_user and db_user["is_active"]:
        end_date = datetime.fromisoformat(db_user["subscription_end"])
        remaining = get_remaining_days(end_date)
        
        await message.answer(
            f"🌟 **به Trade Craft FX خوش آمدید!**\n\n"
            f"✅ شما هم‌اکنون کاربر VIP هستید.\n"
            f"📅 تاریخ انقضا: {to_jalali_full(end_date)}\n"
            f"⏳ روزهای باقی‌مانده: **{remaining} روز**\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🌟 **به Trade Craft FX خوش آمدید!**\n\n"
            "برای دسترسی به محتوای VIP، ابتدا اشتراک خود را تهیه کنید.\n\n"
            "💎 **پلن‌های ویژه:**\n"
            f"• یک ماهه: {Config.PRICES['1m']} دلار\n"
            f"• سه ماهه: {Config.PRICES['3m']} دلار\n"
            f"• شش ماهه: {Config.PRICES['6m']} دلار\n"
            f"• یک ساله: {Config.PRICES['12m']} دلار\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== خرید اشتراک ====================

@router.callback_query(lambda c: c.data == "buy")
async def buy_subscription(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📅 **لطفاً پلن مورد نظر خود را انتخاب کنید:**",
        reply_markup=get_plans_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("plan_"))
async def select_plan(callback: types.CallbackQuery):
    plan_key = callback.data.replace("plan_", "")
    plan = Config.PLANS.get(plan_key)
    
    if not plan:
        await callback.answer("❌ پلن نامعتبر!", show_alert=True)
        return
    
    price = Config.PRICES[plan_key]
    
    text = (
        f"💎 **پلن {plan['name']}**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 قیمت: **{price} دلار**\n"
        f"📅 مدت: **{plan['months']} ماه**\n\n"
        f"لطفاً روش پرداخت خود را انتخاب کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_methods_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== پرداخت ====================

@router.callback_query(lambda c: c.data.startswith("payment_"))
async def show_payment_info(callback: types.CallbackQuery):
    method = callback.data.replace("payment_", "")
    plan_key = "1m"
    
    payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    if method == "card":
        text = (
            f"💳 **پرداخت کارت به کارت**\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏦 شماره کارت:\n`{Config.CARD_NUMBER}`\n"
            f"👤 نام صاحب کارت: {Config.CARD_OWNER}\n\n"
            f"💰 مبلغ: {Config.PRICES[plan_key]} دلار\n\n"
            f"پس از واریز، روی دکمه **«پرداخت انجام شد»** کلیک کنید."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_confirm_payment_keyboard(payment_id),
            parse_mode="Markdown"
        )
    elif method == "crypto":
        text = (
            f"🪙 **پرداخت با ارز دیجیتال**\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💎 نوع ارز: {Config.CRYPTO_TYPE}\n"
            f"🌐 شبکه: {Config.CRYPTO_NETWORK}\n"
            f"📬 آدرس کیف پول:\n`{Config.CRYPTO_WALLET}`\n\n"
            f"💰 مبلغ: {Config.PRICES[plan_key]} دلار\n\n"
            f"پس از واریز، روی دکمه **«پرداخت انجام شد»** کلیک کنید."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_confirm_payment_keyboard(payment_id),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "🌐 **درگاه پرداخت آنلاین**\n\n"
            "لطفاً از طریق لینک زیر اقدام به پرداخت کنید:\n\n"
            f"🔗 [پرداخت آنلاین](https://your-gateway.com/pay/{payment_id})\n\n"
            "پس از پرداخت، به‌طور خودکار تأیید می‌شوید.",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()

# ==================== تأیید پرداخت ====================

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    payment_id = callback.data.replace("confirm_", "")
    
    await create_transaction(
        user_id=callback.from_user.id,
        amount=Config.PRICES["1m"],
        plan="1m",
        payment_method="card",
        payment_id=payment_id
    )
    
    for admin_id in Config.ADMINS:
        await callback.bot.send_message(
            chat_id=admin_id,
            text=(
                f"🔔 **درخواست تأیید پرداخت جدید**\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"👤 کاربر: {callback.from_user.first_name}\n"
                f"🆔 شناسه: `{callback.from_user.id}`\n"
                f"📌 شناسه پرداخت: `{payment_id}`\n"
                f"💰 مبلغ: {Config.PRICES['1m']} دلار\n\n"
                f"برای تأیید از پنل مدیریت استفاده کنید."
            ),
            parse_mode="Markdown"
        )
    
    await callback.message.edit_text(
        "✅ **درخواست شما به ادمین ارسال شد.**\n\n"
        "پس از تأیید، اشتراک شما فعال خواهد شد.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== وضعیت اشتراک ====================

@router.callback_query(lambda c: c.data == "status")
async def show_status(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if not user or not user["is_active"]:
        await callback.message.edit_text(
            "❌ **شما اشتراک فعالی ندارید.**",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    end_date = datetime.fromisoformat(user["subscription_end"])
    remaining = get_remaining_days(end_date)
    
    text = (
        f"📊 **وضعیت اشتراک شما**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💎 پلن: {Config.PLANS[user['plan']]['name']}\n"
        f"📅 تاریخ پایان: {to_jalali_full(end_date)}\n"
        f"⏳ روزهای باقی‌مانده: **{remaining} روز**\n"
        f"📊 وضعیت: {'✅ فعال' if user['is_active'] else '❌ غیرفعال'}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== حساب کاربری ====================

@router.callback_query(lambda c: c.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    transactions = await get_transactions_by_user(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    total_paid = sum(t["amount"] for t in transactions if t["status"] == "paid")
    
    text = (
        f"👤 **حساب کاربری**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🆔 شناسه: `{user['user_id']}`\n"
        f"👤 نام: {user['first_name'] or 'ندارد'}\n"
        f"📅 تاریخ ثبت‌نام: {to_jalali_full(datetime.fromisoformat(user['registered_at']))}\n"
        f"💰 کل پرداختی: {total_paid} دلار\n"
        f"📊 وضعیت: {'✅ فعال' if user['is_active'] else '❌ غیرفعال'}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== پشتیبانی ====================

@router.callback_query(lambda c: c.data == "support")
async def show_support(callback: types.CallbackQuery):
    text = (
        "📞 **پشتیبانی**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 پشتیبان ۱: {Config.SUPPORT_IDS[0]}\n"
        f"👤 پشتیبان ۲: {Config.SUPPORT_IDS[1]}\n"
        f"👤 پشتیبان ۳: {Config.SUPPORT_IDS[2]}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== راهنما ====================

@router.callback_query(lambda c: c.data == "help")
async def show_help(callback: types.CallbackQuery):
    text = (
        "📚 **آموزش استفاده از ربات**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **خرید اشتراک**\n"
        f"   از منوی اصلی گزینه «خرید اشتراک» را انتخاب کنید.\n\n"
        f"2️⃣ **تمدید اشتراک**\n"
        f"   اگر اشتراک فعال دارید، از گزینه «تمدید اشتراک» استفاده کنید.\n\n"
        f"3️⃣ **مشاهده وضعیت**\n"
        f"   با انتخاب «وضعیت اشتراک» روزهای باقی‌مانده را ببینید.\n\n"
        f"4️⃣ **پشتیبانی**\n"
        f"   در صورت نیاز از بخش پشتیبانی استفاده کنید."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== تمدید اشتراک ====================

@router.callback_query(lambda c: c.data == "renew")
async def renew_subscription(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if not user or not user["is_active"]:
        await callback.answer("❌ شما اشتراک فعالی ندارید!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💳 **تمدید اشتراک**\n\n"
        "لطفاً پلن مورد نظر را انتخاب کنید:",
        reply_markup=get_plans_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== کد تخفیف ====================

@router.callback_query(lambda c: c.data == "discount")
async def show_discount(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 **کد تخفیف**\n\n"
        "برای اعمال کد تخفیف:\n"
        "`/discount کد_تخفیف`\n\n"
        "مثال: `/discount SUMMER20`",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== دکمه بازگشت ====================

@router.callback_query(lambda c: c.data == "back")
async def go_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🌟 **به منوی اصلی خوش آمدید**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
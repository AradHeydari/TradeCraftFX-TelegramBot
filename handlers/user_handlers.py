import uuid
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import Config
from database.repository import (
    get_user, create_user, update_user_subscription,
    create_transaction, get_transactions_by_user,
    get_discount, use_discount
)
from keyboards.inline import (
    get_main_keyboard, get_plans_keyboard,
    get_payment_methods_keyboard, get_confirm_payment_keyboard,
    get_back_keyboard
)
from utils.jalali import to_jalali_full, get_remaining_days
from database.repository import get_price

router = Router()

# ==================== وضعیت‌های FSM ====================

class PaymentStates(StatesGroup):
    waiting_for_payment = State()
    waiting_for_receipt = State()  # ✅ جدید

# ==================== دستور /start ====================

@router.message(Command("start"))
async def start_command(message: types.Message):
    from database.repository import get_price, get_user, create_user
    
    user = message.from_user
    await create_user(user.id, user.username, user.first_name)
    
    db_user = await get_user(user.id)
    
    if db_user and db_user["is_active"]:
        # کاربر فعال است
        from utils.jalali import to_jalali_full, get_remaining_days
        from datetime import datetime
        
        end_date = datetime.fromisoformat(db_user["subscription_end"])
        remaining = get_remaining_days(end_date)
        
        await message.answer(
            f"🌟 **به ایران کریپتو خوش آمدید!**\n\n"
            f"✅ شما هم‌اکنون کاربر VIP هستید.\n"
            f"📅 تاریخ انقضا: {to_jalali_full(end_date)}\n"
            f"⏳ روزهای باقی‌مانده: **{remaining} روز**\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # کاربر غیرفعال است
        price_1m = await get_price("1m")
        price_3m = await get_price("3m")
        price_6m = await get_price("6m")
        price_12m = await get_price("12m")
        
        await message.answer(
            f"🌟 **به ایران کریپتو خوش آمدید!**\n\n"
            "برای دسترسی به محتوای VIP، ابتدا اشتراک خود را تهیه کنید.\n\n"
            "💎 **پلن‌های ویژه:**\n"
            f"• یک ماهه: {price_1m} دلار\n"
            f"• سه ماهه: {price_3m} دلار\n"
            f"• شش ماهه: {price_6m} دلار\n"
            f"• یک ساله: {price_12m} دلار\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== خرید اشتراک ====================

@router.callback_query(lambda c: c.data == "buy")
async def buy_subscription(callback: types.CallbackQuery):
    # دریافت قیمت‌ها از دیتابیس
    prices = {}
    for key in Config.PLANS.keys():
        prices[key] = await get_price(key)
    
    # ساخت متن منو
    text = "📅 **لطفاً پلن مورد نظر خود را انتخاب کنید:**\n\n"
    for key, plan in Config.PLANS.items():
        text += f"• {plan['name']}: {prices[key]} دلار\n"
    
    # ارسال کیبورد با قیمت‌های به‌روز
    await callback.message.edit_text(
        text,
        reply_markup=get_plans_keyboard(prices),  # ← قیمت‌ها را به کیبورد می‌دهیم
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("plan_"))
async def select_plan(callback: types.CallbackQuery, state: FSMContext):
    plan_key = callback.data.replace("plan_", "")
    plan = Config.PLANS.get(plan_key)
    
    if not plan:
        await callback.answer("❌ پلن نامعتبر!", show_alert=True)
        return
    
    # ذخیره plan_key در state
    await state.update_data(plan_key=plan_key)
    
    price = await get_price(plan_key)
    
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
async def show_payment_info(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.replace("payment_", "")
    
    # دریافت plan_key از state
    data = await state.get_data()
    plan_key = data.get("plan_key", "1m")
    
    payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    await state.update_data(payment_id=payment_id, plan_key=plan_key)
    
    price = Config.PRICES[plan_key]
    
    if method == "card":
        text = (
            f"💳 **پرداخت کارت به کارت**\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏦 شماره کارت:\n`{Config.CARD_NUMBER}`\n"
            f"👤 نام صاحب کارت: {Config.CARD_OWNER}\n\n"
            f"💰 مبلغ: **{price} دلار**\n\n"
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
            f"💰 مبلغ: **{price} دلار**\n\n"
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

# ==================== تأیید پرداخت (کاربر) ====================

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    payment_id = callback.data.replace("confirm_", "")
    
    # دریافت plan_key از state
    data = await state.get_data()
    plan_key = data.get("plan_key", "1m")
    
    # ✅ ذخیره اطلاعات در state برای مرحله بعد
    await state.update_data(
        payment_id=payment_id,
        plan_key=plan_key,
        user_id=callback.from_user.id,
        user_name=callback.from_user.first_name
    )
    
    # ✅ تغییر وضعیت به waiting_for_receipt
    await state.set_state(PaymentStates.waiting_for_receipt)
    
    # ✅ درخواست عکس از کاربر
    await callback.message.edit_text(
        "📸 **لطفاً عکس رسید پرداخت خود را ارسال کنید.**\n\n"
        "پس از ارسال عکس، درخواست شما برای ادمین ارسال خواهد شد.\n\n"
        "⏳ اگر عکس ندارید، روی دکمه **«لغو»** کلیک کنید.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ لغو", callback_data="cancel_payment")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== وضعیت اشتراک ====================

@router.callback_query(lambda c: c.data == "status")
async def show_status(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if not user or not user["is_active"]:
        await callback.message.edit_text(
            "❌ **شما اشتراک فعالی ندارید.**\n\n"
            "لطفاً از بخش خرید اشتراک، یک پلن تهیه کنید.",
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
        f"📅 تاریخ شروع: {to_jalali_full(datetime.fromisoformat(user['subscription_start']))}\n"
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
        f"📛 نام کاربری: @{user['username'] or 'ندارد'}\n"
        f"📅 تاریخ ثبت‌نام: {to_jalali_full(datetime.fromisoformat(user['registered_at']))}\n"
        f"💰 کل پرداختی: {total_paid} دلار\n"
        f"📊 وضعیت: {'✅ فعال' if user['is_active'] else '❌ غیرفعال'}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== تمدید اشتراک ====================

@router.callback_query(lambda c: c.data == "renew")
async def renew_subscription(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if not user or not user["is_active"]:
        await callback.answer("❌ شما اشتراک فعالی ندارید!", show_alert=True)
        return
    
    # دریافت قیمت‌ها از دیتابیس
    prices = {}
    for key in Config.PLANS.keys():
        prices[key] = await get_price(key)
    
    await callback.message.edit_text(
        "💳 **تمدید اشتراک**\n\n"
        "لطفاً پلن مورد نظر برای تمدید را انتخاب کنید:",
        reply_markup=get_plans_keyboard(prices),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== پشتیبانی ====================

@router.callback_query(lambda c: c.data == "support")
async def show_support(callback: types.CallbackQuery):
    text = (
        "📞 **پشتیبانی**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"برای ارتباط با پشتیبانی، از طریق یکی از راه‌های زیر اقدام کنید:\n\n"
        f"👤 پشتیبان ۱: {Config.SUPPORT_IDS[0]}\n"
        f"👤 پشتیبان ۲: {Config.SUPPORT_IDS[1]}\n"
        f"👤 پشتیبان ۳: {Config.SUPPORT_IDS[2]}\n\n"
        f"یا از طریق ربات تیکت ثبت کنید."
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
        f"   از منوی اصلی گزینه «خرید اشتراک» را انتخاب کنید.\n"
        f"   سپس پلن مورد نظر و روش پرداخت را انتخاب کنید.\n\n"
        f"2️⃣ **تمدید اشتراک**\n"
        f"   اگر اشتراک فعال دارید، از گزینه «تمدید اشتراک» استفاده کنید.\n\n"
        f"3️⃣ **مشاهده وضعیت**\n"
        f"   با انتخاب «وضعیت اشتراک» می‌توانید روزهای باقی‌مانده را ببینید.\n\n"
        f"4️⃣ **پشتیبانی**\n"
        f"   در صورت نیاز، از بخش پشتیبانی با ما در ارتباط باشید."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== کد تخفیف ====================

@router.callback_query(lambda c: c.data == "discount")
async def show_discount(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 **کد تخفیف**\n\n"
        "اگر کد تخفیف دارید، آن را وارد کنید:\n\n"
        "`/discount کد_تخفیف`\n\n"
        "مثال: `/discount SUMMER20`",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("discount"))
async def apply_discount(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ لطفاً کد تخفیف را وارد کنید.\nمثال: `/discount SUMMER20`", parse_mode="Markdown")
        return
    
    code = parts[1].upper()
    discount = await get_discount(code)
    
    if not discount:
        await message.answer("❌ کد تخفیف نامعتبر یا منقضی شده است.")
        return
    
    await message.answer(
        f"✅ **کد تخفیف {code} با موفقیت اعمال شد!**\n\n"
        f"🎁 تخفیف: {discount['discount_percent']}%\n"
        f"🔢 تعداد استفاده: {discount['used_count']}/{discount['max_uses']}\n\n"
        f"تخفیف در خرید بعدی شما اعمال خواهد شد."
    )

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


# ===================دریافت عکس====================

@router.message(PaymentStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: types.Message, state: FSMContext):
    """دریافت عکس رسید و ارسال به ادمین"""
    
    # دریافت اطلاعات از state
    data = await state.get_data()
    payment_id = data.get("payment_id")
    plan_key = data.get("plan_key", "1m")
    user_id = data.get("user_id")
    user_name = data.get("user_name", "کاربر")
    
    if not payment_id:
        await message.answer("❌ خطا: اطلاعات پرداخت یافت نشد. لطفاً دوباره تلاش کنید.")
        await state.clear()
        return
    
    # دریافت عکس
    photo = message.photo[-1]  # بهترین کیفیت
    
    # ✅ ثبت تراکنش در دیتابیس (همان کد قبلی)
    await create_transaction(
        user_id=user_id,
        amount=Config.PRICES[plan_key],
        plan=plan_key,
        payment_method="card",
        payment_id=payment_id
    )
    
    # ✅ ارسال عکس + اطلاعات به ادمین (همان کد قبلی + عکس)
    for admin_id in Config.ADMINS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=(
                    f"🔔 **درخواست تأیید پرداخت جدید**\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"👤 کاربر: {user_name}\n"
                    f"🆔 شناسه: `{user_id}`\n"
                    f"📌 شناسه پرداخت: `{payment_id}`\n"
                    f"📅 پلن: {Config.PLANS[plan_key]['name']}\n"
                    f"💰 مبلغ: {Config.PRICES[plan_key]} دلار\n\n"
                    f"🖼️ **رسید پرداخت:** (تصویر بالا)\n\n"
                    f"برای تأیید یا رد، از پنل مدیریت استفاده کنید."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"خطا در ارسال به ادمین: {e}")
    
    # ✅ پیام به کاربر (همان کد قبلی)
    await message.answer(
        "✅ **عکس رسید شما با موفقیت ارسال شد!**\n\n"
        "درخواست شما برای ادمین ارسال شده است.\n"
        "پس از بررسی و تأیید، اشتراک شما فعال خواهد شد.\n\n"
        "🙏 لطفاً صبور باشید.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.clear()



@router.callback_query(lambda c: c.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    """لغو فرآیند پرداخت"""
    await state.clear()
    await callback.message.edit_text(
        "❌ **فرآیند پرداخت لغو شد.**\n\n"
        "در صورت نیاز دوباره تلاش کنید.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(PaymentStates.waiting_for_receipt, F.text)
async def invalid_receipt(message: types.Message):
    """اگر کاربر به جای عکس، متن ارسال کند"""
    await message.answer(
        "❌ **لطفاً یک عکس ارسال کنید.**\n\n"
        "از دکمه 📎 (گیره کاغذ) برای ارسال عکس رسید استفاده کنید.\n\n"
        "اگر نمی‌خواهید ادامه دهید، روی دکمه **«لغو»** کلیک کنید."
    )

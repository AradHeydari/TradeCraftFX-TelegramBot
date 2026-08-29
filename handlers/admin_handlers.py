from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.repository import (
    get_all_users,
    get_all_active_users,
    get_all_transactions,
    get_monthly_income,
    get_user,
    get_expired_users,
    get_expiring_soon_users,
    get_new_users_since,
    get_transactions_by_user,
    update_transaction_status,
    update_user_subscription,
    get_all_discounts,
    create_discount,
    create_broadcast,
    update_broadcast_stats,
    get_all_tickets,
    get_ticket,
    answer_ticket,
    close_ticket,
    set_price as set_price_db,
    get_price,
)
from keyboards.inline import get_admin_panel_keyboard
from utils.jalali import to_jalali_full, get_jalali_month_name, get_remaining_days
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
        parse_mode="Markdown",
    )


# ==================== تغییر قیمت (دائمی) ====================

@router.message(Command("setprice"))
async def set_price(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "❌ فرمت صحیح:\n"
            "`/setprice پلن قیمت`\n"
            "مثال: `/setprice 1m 50`",
            parse_mode="Markdown"
        )
        return
    
    plan_key = parts[1]
    try:
        new_price = int(parts[2])
    except ValueError:
        await message.answer("❌ قیمت باید یک عدد باشد.")
        return
    
    if plan_key not in Config.PLANS:
        await message.answer("❌ پلن نامعتبر! پلن‌های معتبر: 1m, 3m, 6m, 12m")
        return
    
    # ذخیره در دیتابیس
    await set_price_db(plan_key, new_price)
    
    # به‌روزرسانی در حافظه
    Config.PRICES[plan_key] = new_price
    
    await message.answer(
        f"✅ **قیمت پلن {Config.PLANS[plan_key]['name']} به {new_price} دلار تغییر کرد.**\n\n"
        f"📌 این تغییر در دیتابیس ذخیره شد و دائمی است."
    )


# ==================== منوی تغییر قیمت ====================

@router.callback_query(lambda c: c.data == "admin_prices")
async def admin_prices_menu(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    text = "🔧 **تغییر قیمت پلن‌ها**\n━━━━━━━━━━━━━━━━━\n"
    for key, plan in Config.PLANS.items():
        price = await get_price(key)
        text += f"📅 {plan['name']}: **{price}** دلار\n"
    
    text += "\nبرای تغییر قیمت از دستور زیر استفاده کنید:\n"
    text += "`/setprice 1m 50`\n"
    text += "`/setprice 3m 90`\n"
    text += "`/setprice 6m 130`\n"
    text += "`/setprice 12m 250`"
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()


# ==================== مدیریت کاربران ====================

@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users_list(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    users = await get_all_users()
    
    if not users:
        await callback.message.edit_text("📭 **هیچ کاربری یافت نشد.**")
        await callback.answer()
        return
    
    text = "👥 **لیست کاربران**\n━━━━━━━━━━━━━━━━━\n"
    for i, user in enumerate(users[:20], 1):
        status = "✅" if user["is_active"] else "❌"
        username = f"@{user['username']}" if user["username"] else "بدون نام"
        text += f"{i}. {status} {username} (ID: {user['user_id']})\n"
    
    if len(users) > 20:
        text += f"\n... و {len(users) - 20} نفر دیگر"
    
    text += "\n\n🔍 برای مشاهده عملیات روی یک کاربر، روی دکمهٔ زیر کلیک کنید."
    
    buttons = []
    for user in users[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{user['user_id']}",
                callback_data=f"admin_user_{user['user_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_admin")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


def get_admin_user_actions_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 تمدید اشتراک", callback_data=f"admin_renew_{user_id}")],
            [InlineKeyboardButton(text="❌ غیرفعال کردن", callback_data=f"admin_deactivate_{user_id}")],
            [InlineKeyboardButton(text="📋 تاریخچه تراکنش", callback_data=f"admin_user_trans_{user_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_users")],
        ]
    )


@router.callback_query(lambda c: c.data.startswith("admin_user_"))
async def admin_user_detail(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    user_id = int(callback.data.replace("admin_user_", ""))
    user = await get_user(user_id)
    
    if not user:
        await callback.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    text = (
        f"👤 **اطلاعات کاربر**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🆔 شناسه: `{user['user_id']}`\n"
        f"👤 نام: {user['first_name'] or 'ندارد'}\n"
        f"📛 نام کاربری: @{user['username'] or 'ندارد'}\n"
        f"📅 ثبت‌نام: {to_jalali_full(datetime.fromisoformat(user['registered_at']))}\n"
        f"💎 پلن: {Config.PLANS.get(user['plan'], {}).get('name', 'ندارد')}\n"
        f"📊 وضعیت: {'✅ فعال' if user['is_active'] else '❌ غیرفعال'}"
    )
    
    if user["subscription_end"]:
        end_date = datetime.fromisoformat(user["subscription_end"])
        remaining = get_remaining_days(end_date)
        text += f"\n⏳ باقی‌مانده: {remaining} روز"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_user_actions_keyboard(user_id),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin_renew_"))
async def admin_renew_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    user_id = int(callback.data.replace("admin_renew_", ""))
    user = await get_user(user_id)
    
    if not user:
        await callback.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    await update_user_subscription(
        user_id=user_id,
        plan=user["plan"] or "1m",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        active=True,
    )
    
    await callback.message.edit_text(
        f"✅ **اشتراک کاربر {user_id} با موفقیت تمدید شد.**\n\n"
        f"📅 تاریخ جدید: {to_jalali_full(end_date)}",
        parse_mode="Markdown"
    )
    await callback.answer("✅ تمدید شد!")


@router.callback_query(lambda c: c.data.startswith("admin_deactivate_"))
async def admin_deactivate_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    user_id = int(callback.data.replace("admin_deactivate_", ""))
    user = await get_user(user_id)
    
    if not user:
        await callback.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    await update_user_subscription(
        user_id=user_id,
        plan=user["plan"],
        start_date=user["subscription_start"],
        end_date=user["subscription_end"],
        active=False,
    )
    
    await callback.message.edit_text(
        f"❌ **کاربر {user_id} غیرفعال شد.**",
        parse_mode="Markdown"
    )
    await callback.answer("✅ غیرفعال شد!")


@router.callback_query(lambda c: c.data.startswith("admin_user_trans_"))
async def admin_user_transactions(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    user_id = int(callback.data.replace("admin_user_trans_", ""))
    transactions = await get_transactions_by_user(user_id)
    
    if not transactions:
        await callback.message.edit_text(f"📭 **کاربر {user_id} هیچ تراکنشی ندارد.**")
        await callback.answer()
        return
    
    text = f"📋 **تراکنش‌های کاربر {user_id}**\n━━━━━━━━━━━━━━━━━\n"
    for t in transactions[:20]:
        status_icon = "✅" if t["status"] == "paid" else "⏳" if t["status"] == "pending" else "❌"
        text += f"{status_icon} {t['amount']}$ - {t['plan']} - {t['payment_method']}\n"
    
    if len(transactions) > 20:
        text += f"\n... و {len(transactions) - 20} تراکنش دیگر"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


# ==================== آمار کلی ====================

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    users = await get_all_users()
    active_users = await get_all_active_users()
    expired_users = await get_expired_users()
    expiring_soon = await get_expiring_soon_users(7)
    
    start_of_month = datetime(datetime.now().year, datetime.now().month, 1).isoformat()
    new_users = await get_new_users_since(start_of_month)
    
    income = await get_monthly_income(datetime.now().year, datetime.now().month)
    
    text = (
        f"📊 **آمار کلی ربات**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 کل کاربران: {len(users)}\n"
        f"✅ کاربران فعال: {len(active_users)}\n"
        f"❌ کاربران منقضی: {len(expired_users)}\n"
        f"⏳ در حال انقضا (۷ روز): {len(expiring_soon)}\n"
        f"🆕 کاربران جدید این ماه: {len(new_users)}\n"
        f"💰 درآمد این ماه: {income:,} دلار\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📅 {get_jalali_month_name(datetime.now())}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()


# ==================== لیست تراکنش‌ها ====================

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
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_admin")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin_confirm_"))
async def admin_confirm_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    payment_id = callback.data.replace("admin_confirm_", "")
    
    await update_transaction_status(payment_id, "paid")
    
    from database.repository import get_transaction
    transaction = await get_transaction(payment_id)
    
    if transaction:
        user_id = transaction["user_id"]
        plan_key = transaction["plan"]
        amount = transaction["amount"]
        try:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=Config.PLANS[plan_key]["months"] * 30)
            
            await update_user_subscription(
                user_id=user_id,
                plan=plan_key,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                active=True,
            )
            
            # ========== پیام تأیید پرداخت ==========
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ **پرداخت شما با موفقیت تأیید شد!**\n\n"
                    f"📌 شناسه پرداخت: `{payment_id}`\n"
                    f"💰 مبلغ: {amount} دلار\n"
                    f"📅 پلن: {Config.PLANS[plan_key]['name']}\n\n"
                    f"📅 تاریخ انقضا: {to_jalali_full(end_date)}\n\n"
                    f"🎉 اشتراک شما فعال شد. از خدمات ما لذت ببرید!"
                ),
                parse_mode="Markdown"
            )
            
            # ========== ارسال لینک کانال خصوصی VIP ==========
            if Config.PRIVATE_CHANNEL_LINK:
                try:
                    await callback.bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"🔗 **لینک کانال خصوصی VIP:**\n\n"
                            f"{Config.PRIVATE_CHANNEL_LINK}\n\n"
                            f"برای دسترسی به محتوای VIP، روی لینک کلیک کنید."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"خطا در ارسال لینک کانال به کاربر {user_id}: {e}")
            else:
                print("⚠️ لینک کانال خصوصی در .env تنظیم نشده است.")
            
        except Exception as e:
            print(f"خطا در تأیید پرداخت: {e}")
    
    await callback.message.edit_text(
        f"✅ **پرداخت با شناسه `{payment_id}` تأیید شد.**\n\nبه کاربر اطلاع‌رسانی شد.",
        parse_mode="Markdown"
    )
    await callback.answer("✅ پرداخت تأیید شد!")


@router.callback_query(lambda c: c.data.startswith("admin_reject_"))
async def admin_reject_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    payment_id = callback.data.replace("admin_reject_", "")
    
    await update_transaction_status(payment_id, "failed")
    
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
        f"❌ **پرداخت با شناسه `{payment_id}` رد شد.**\n\nبه کاربر اطلاع‌رسانی شد.",
        parse_mode="Markdown"
    )
    await callback.answer("❌ پرداخت رد شد!")


# ==================== مدیریت تخفیف‌ها ====================

@router.callback_query(lambda c: c.data == "admin_discounts")
async def admin_discounts(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    discounts = await get_all_discounts()
    
    text = "🎁 **لیست کدهای تخفیف**\n━━━━━━━━━━━━━━━━━\n"
    if discounts:
        for d in discounts:
            status = "✅" if d["is_active"] else "❌"
            text += f"{status} {d['code']} - {d['discount_percent']}% ({d['used_count']}/{d['max_uses']})\n"
    else:
        text += "📭 هیچ کد تخفیفی وجود ندارد."
    
    text += (
        "\n\nبرای ایجاد کد تخفیف جدید:\n"
        "`/newdiscount کد درصد تعداد_استفاده`\n"
        "مثال: `/newdiscount SUMMER20 20 100`"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()


@router.message(Command("newdiscount"))
async def create_new_discount(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "❌ فرمت صحیح:\n"
            "`/newdiscount کد درصد تعداد_استفاده`\n"
            "مثال: `/newdiscount SUMMER20 20 100`",
            parse_mode="Markdown"
        )
        return
    
    code = parts[1].upper()
    percent = int(parts[2])
    max_uses = int(parts[3])
    
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    
    await create_discount(code, percent, max_uses, expires_at)
    
    await message.answer(
        f"✅ **کد تخفیف با موفقیت ساخته شد!**\n\n"
        f"🎁 کد: `{code}`\n"
        f"📊 درصد تخفیف: {percent}%\n"
        f"🔢 حداکثر استفاده: {max_uses}\n"
        f"📅 اعتبار: ۳۰ روز"
    )


# ==================== پیام همگانی ====================

@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    from keyboards.inline import get_back_keyboard
    
    await callback.message.edit_text(
        "📨 **ارسال پیام همگانی**\n\n"
        "لطفاً پیام خود را ارسال کنید.\n"
        "(متن، تصویر، ویدئو یا هر نوع فایل دیگری)\n\n"
        "⚠️ پیام برای **همه کاربران** ارسال خواهد شد.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# فقط پیام‌های ادمین را بگیر و اگر با / شروع نشده باشد
@router.message(F.text & ~F.text.startswith("/"))
async def broadcast_send(message: types.Message):
    # فقط ادمین می‌تواند پیام همگانی بفرستد
    if not await is_admin(message.from_user.id):
        return
    
    users = await get_all_users()
    
    sent_count = 0
    failed_count = 0
    
    broadcast_id = await create_broadcast(message.text or "پیام همگانی")
    
    for user in users:
        try:
            await message.bot.send_message(
                chat_id=user["user_id"],
                text=message.text,
                parse_mode="Markdown" if message.text else None,
            )
            sent_count += 1
        except Exception:
            failed_count += 1
    
    await update_broadcast_stats(broadcast_id, sent_count, failed_count)
    
    await message.answer(
        f"✅ **پیام همگانی ارسال شد!**\n\n"
        f"📤 ارسال شده: {sent_count}\n"
        f"❌ ناموفق: {failed_count}"
    )


# ==================== مدیریت تیکت‌ها ====================

@router.callback_query(lambda c: c.data == "admin_tickets")
async def admin_tickets_list(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    tickets = await get_all_tickets()
    open_tickets = [t for t in tickets if t["status"] == "open"]
    
    text = "📞 **مدیریت تیکت‌ها**\n━━━━━━━━━━━━━━━━━\n"
    text += f"🟢 تیکت‌های باز: {len(open_tickets)}\n"
    text += f"📊 کل تیکت‌ها: {len(tickets)}\n\n"
    
    if open_tickets:
        for t in open_tickets[:10]:
            text += f"📌 #{t['id']} - کاربر {t['user_id']}: {t['subject'][:20]}...\n"
        text += "\nبرای پاسخ، روی شناسه تیکت کلیک کنید."
        
        buttons = []
        for t in open_tickets[:10]:
            buttons.append([
                InlineKeyboardButton(
                    text=f"#{t['id']} - {t['subject'][:15]}",
                    callback_data=f"admin_ticket_{t['id']}"
                )
            ])
        buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_admin")])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text + "✅ همه تیکت‌ها پاسخ داده شده‌اند.",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin_ticket_"))
async def admin_ticket_detail(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    ticket_id = int(callback.data.replace("admin_ticket_", ""))
    ticket = await get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ تیکت یافت نشد!", show_alert=True)
        return
    
    user = await get_user(ticket["user_id"])
    username = f"@{user['username']}" if user and user["username"] else f"کاربر {ticket['user_id']}"
    
    text = (
        f"📋 **تیکت #{ticket['id']}**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {username}\n"
        f"📌 موضوع: {ticket['subject']}\n"
        f"📝 پیام: {ticket['message']}\n"
        f"📊 وضعیت: {ticket['status']}\n"
        f"📅 تاریخ: {ticket['created_at']}\n"
    )
    
    if ticket["answer"]:
        text += f"\n💬 **پاسخ شما:**\n{ticket['answer']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ پاسخ به تیکت", callback_data=f"ticket_answer_{ticket_id}")],
                [InlineKeyboardButton(text="❌ بستن تیکت", callback_data=f"ticket_close_{ticket_id}")],
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_tickets")],
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("ticket_answer_"))
async def admin_answer_ticket(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    ticket_id = int(callback.data.replace("ticket_answer_", ""))
    ticket = await get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ تیکت یافت نشد!", show_alert=True)
        return
    
    from keyboards.inline import get_back_keyboard
    
    await callback.message.edit_text(
        f"✏️ **پاسخ به تیکت #{ticket_id}**\n\n"
        f"لطفاً پاسخ خود را به صورت زیر ارسال کنید:\n"
        f"`/answerticket {ticket_id} پاسخ شما`\n\n"
        f"مثال: `/answerticket {ticket_id} مشکل شما برطرف شد.`",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("answerticket"))
async def admin_send_answer(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "❌ فرمت صحیح:\n"
            "`/answerticket شناسه پاسخ`\n"
            "مثال: `/answerticket 1 مشکل شما برطرف شد.`",
            parse_mode="Markdown"
        )
        return
    
    ticket_id = int(parts[1])
    answer_text = parts[2]
    
    ticket = await get_ticket(ticket_id)
    if not ticket:
        await message.answer("❌ تیکت یافت نشد.")
        return
    
    await answer_ticket(ticket_id, answer_text)
    
    try:
        await message.bot.send_message(
            chat_id=ticket["user_id"],
            text=(
                f"💬 **پاسخ به تیکت #{ticket_id}**\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{answer_text}\n\n"
                f"وضعیت تیکت: پاسخ داده شده ✅"
            ),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    
    await message.answer(f"✅ **پاسخ به تیکت #{ticket_id} ارسال شد.**")


@router.callback_query(lambda c: c.data.startswith("ticket_close_"))
async def admin_close_ticket(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    ticket_id = int(callback.data.replace("ticket_close_", ""))
    await close_ticket(ticket_id)
    
    await callback.message.edit_text(
        f"✅ **تیکت #{ticket_id} بسته شد.**",
        parse_mode="Markdown"
    )
    await callback.answer("✅ تیکت بسته شد!")


# ==================== گزارش فروش ====================

@router.callback_query(lambda c: c.data == "admin_sales_report")
async def admin_sales_report(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    transactions = await get_all_transactions()
    paid_transactions = [t for t in transactions if t["status"] == "paid"]
    
    total_income = sum(t["amount"] for t in paid_transactions)
    monthly_income = await get_monthly_income(datetime.now().year, datetime.now().month)
    
    text = (
        f"📈 **گزارش فروش**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 کل درآمد: {total_income:,} دلار\n"
        f"📊 درآمد این ماه: {monthly_income:,} دلار\n"
        f"✅ تراکنش‌های موفق: {len(paid_transactions)}\n"
        f"⏳ در انتظار: {len([t for t in transactions if t['status'] == 'pending'])}\n"
        f"❌ ناموفق: {len([t for t in transactions if t['status'] == 'failed'])}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📅 {get_jalali_month_name(datetime.now())}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()


# ==================== بازگشت به پنل ====================

@router.callback_query(lambda c: c.data == "back_admin")
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👑 **پنل مدیریت**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
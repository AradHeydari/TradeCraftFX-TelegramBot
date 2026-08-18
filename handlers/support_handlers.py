from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
from database.repository import (
    create_ticket, get_ticket, get_user_tickets,
    get_all_tickets, answer_ticket, close_ticket, get_user
)
from keyboards.inline import get_back_keyboard, get_main_keyboard
from utils.helpers import is_admin
from config import Config

router = Router()

# ==================== وضعیت‌های FSM ====================

class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()

# ==================== مشاهده تیکت‌ها (کاربر) ====================

@router.message(Command("tickets"))
async def show_user_tickets(message: types.Message):
    tickets = await get_user_tickets(message.from_user.id)
    
    if not tickets:
        await message.answer("📭 **شما هیچ تیکتی ثبت نکرده‌اید.**")
        return
    
    text = "📋 **لیست تیکت‌های شما**\n━━━━━━━━━━━━━━━━━\n"
    for t in tickets:
        status_icon = "🟢" if t["status"] == "open" else "🟡" if t["status"] == "answered" else "🔴"
        text += f"{status_icon} #{t['id']} - {t['subject']} ({t['status']})\n"
    
    text += "\nبرای مشاهده جزئیات: `/ticket شناسه`"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("ticket"))
async def show_ticket_detail(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ لطفاً شناسه تیکت را وارد کنید.\nمثال: `/ticket 1`")
        return
    
    ticket_id = int(parts[1])
    ticket = await get_ticket(ticket_id)
    
    if not ticket:
        await message.answer("❌ تیکت یافت نشد.")
        return
    
    if ticket["user_id"] != message.from_user.id and not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این تیکت را ندارید.")
        return
    
    text = (
        f"📋 **تیکت #{ticket['id']}**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📌 موضوع: {ticket['subject']}\n"
        f"📝 پیام: {ticket['message']}\n"
        f"📊 وضعیت: {ticket['status']}\n"
        f"📅 تاریخ: {ticket['created_at']}\n"
    )
    
    if ticket["answer"]:
        text += f"\n💬 **پاسخ پشتیبانی:**\n{ticket['answer']}"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== ثبت تیکت جدید ====================

@router.callback_query(lambda c: c.data == "support")
async def show_support_options(callback: types.CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = (
        "📞 **پشتیبانی**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"برای ارتباط با پشتیبانی، از یکی از روش‌های زیر استفاده کنید:\n\n"
        f"👤 پشتیبان ۱: {Config.SUPPORT_IDS[0]}\n"
        f"👤 پشتیبان ۲: {Config.SUPPORT_IDS[1]}\n"
        f"👤 پشتیبان ۳: {Config.SUPPORT_IDS[2]}\n\n"
        f"📝 **یا از طریق ربات تیکت ثبت کنید:**"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 ثبت تیکت جدید", callback_data="new_ticket")],
                [InlineKeyboardButton(text="📋 مشاهده تیکت‌ها", callback_data="my_tickets")],
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")],
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "new_ticket")
async def start_new_ticket(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TicketStates.waiting_for_subject)
    await callback.message.edit_text(
        "📝 **ثبت تیکت پشتیبانی**\n\n"
        "لطفاً **موضوع** تیکت خود را وارد کنید:\n"
        "(مثلاً: مشکل در پرداخت، مشکل دسترسی و ...)",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(TicketStates.waiting_for_subject, F.text)
async def ticket_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(TicketStates.waiting_for_message)
    await message.answer(
        "📝 **پیام خود را وارد کنید:**\n\n"
        "توضیحات کامل مشکل یا درخواست خود را بنویسید.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(TicketStates.waiting_for_message, F.text)
async def ticket_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    subject = data.get("subject")
    ticket_message = message.text
    
    await create_ticket(
        user_id=message.from_user.id,
        subject=subject,
        message=ticket_message
    )
    
    await state.clear()
    await message.answer(
        "✅ **تیکت شما با موفقیت ثبت شد!**\n\n"
        "پشتیبانی در اسرع وقت پاسخ خواهد داد.\n"
        "شما می‌توانید تاریخچه تیکت‌های خود را با دستور `/tickets` مشاهده کنید.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(lambda c: c.data == "my_tickets")
async def view_my_tickets(callback: types.CallbackQuery):
    tickets = await get_user_tickets(callback.from_user.id)
    
    if not tickets:
        await callback.message.edit_text(
            "📭 **شما هیچ تیکتی ثبت نکرده‌اید.**",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    text = "📋 **لیست تیکت‌های شما**\n━━━━━━━━━━━━━━━━━\n"
    for t in tickets[:10]:
        status_icon = "🟢" if t["status"] == "open" else "🟡" if t["status"] == "answered" else "🔴"
        text += f"{status_icon} #{t['id']} - {t['subject']} ({t['status']})\n"
    
    if len(tickets) > 10:
        text += f"\n... و {len(tickets) - 10} تیکت دیگر"
    
    text += "\n\nبرای مشاهده جزئیات: `/ticket شناسه`"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== مدیریت تیکت‌ها (ادمین) ====================

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
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
            reply_markup=get_back_keyboard(),
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
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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
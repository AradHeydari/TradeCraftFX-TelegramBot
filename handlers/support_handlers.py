from aiogram import Router, types, F
from aiogram.filters import Command
from database.repository import create_ticket, get_user_tickets, get_ticket
from config import Config
from keyboards.inline import get_back_keyboard

router = Router()

@router.message(Command("tickets"))
async def show_user_tickets(message: types.Message):
    tickets = await get_user_tickets(message.from_user.id)
    if not tickets:
        await message.answer("📭 شما هیچ تیکتی ندارید.")
        return
    text = "📋 **لیست تیکت‌ها**\n"
    for t in tickets:
        status_icon = "🟢" if t["status"] == "open" else "🟡" if t["status"] == "answered" else "🔴"
        text += f"{status_icon} #{t['id']} - {t['subject']}\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("ticket"))
async def show_ticket_detail(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ شناسه تیکت را وارد کنید.")
        return
    ticket_id = int(parts[1])
    ticket = await get_ticket(ticket_id)
    if not ticket:
        await message.answer("❌ تیکت یافت نشد.")
        return
    if ticket["user_id"] != message.from_user.id:
        await message.answer("⛔ دسترسی غیرمجاز!")
        return
    text = (
        f"📋 **تیکت #{ticket['id']}**\n"
        f"📌 موضوع: {ticket['subject']}\n"
        f"📝 پیام: {ticket['message']}\n"
        f"📊 وضعیت: {ticket['status']}"
    )
    if ticket["answer"]:
        text += f"\n💬 پاسخ: {ticket['answer']}"
    await message.answer(text, parse_mode="Markdown")
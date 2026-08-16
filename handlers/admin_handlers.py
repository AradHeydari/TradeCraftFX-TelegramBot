from aiogram import Router, types
from aiogram.filters import Command
from keyboards.inline import get_back_keyboard

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    await message.answer(
        "👑 **پنل مدیریت**\n\n"
        "این بخش در حال تکمیل است.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
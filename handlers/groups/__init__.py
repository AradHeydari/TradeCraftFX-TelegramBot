"""Group chat handlers — add yours here."""
from __future__ import annotations

from aiogram import Router

router = Router(name="groups")

# Example: filter to only handle group/supergroup messages
# from aiogram.enums import ChatType
# router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))

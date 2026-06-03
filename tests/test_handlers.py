"""Unit tests for handlers (no bot instance required — uses mocks)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from handlers.users.callbacks import demo_premium_callback, demo_regular_callback
from handlers.users.echo import echo_handler
from handlers.users.help import help_handler
from handlers.users.start import start_handler


async def test_start_handler_greets_user() -> None:
    message = AsyncMock()
    message.from_user = MagicMock(full_name="Test User")

    await start_handler(message)

    message.answer.assert_called_once()
    assert "Test User" in message.answer.call_args.args[0]


async def test_start_handler_passes_keyboard() -> None:
    message = AsyncMock()
    message.from_user = MagicMock(full_name="Test User")

    await start_handler(message)

    kwargs = message.answer.call_args.kwargs
    assert kwargs.get("reply_markup") is not None


async def test_start_handler_keyboard_has_icon_button() -> None:
    message = AsyncMock()
    message.from_user = MagicMock(full_name="Test User")

    await start_handler(message)

    kb = message.answer.call_args.kwargs["reply_markup"]
    btn = kb.inline_keyboard[0][0]
    assert btn.icon_custom_emoji_id is not None


async def test_help_handler_lists_commands() -> None:
    message = AsyncMock()

    await help_handler(message)

    message.answer.assert_called_once()
    text = message.answer.call_args.args[0]
    assert "/start" in text
    assert "/help" in text


async def test_help_handler_passes_keyboard() -> None:
    message = AsyncMock()

    await help_handler(message)

    kwargs = message.answer.call_args.kwargs
    assert kwargs.get("reply_markup") is not None


async def test_demo_premium_callback_answers() -> None:
    callback = AsyncMock()

    await demo_premium_callback(callback)

    callback.answer.assert_called_once()


async def test_demo_regular_callback_answers() -> None:
    callback = AsyncMock()

    await demo_regular_callback(callback)

    callback.answer.assert_called_once()


async def test_echo_handler_returns_same_text() -> None:
    message = AsyncMock()
    message.text = "hello world"

    await echo_handler(message)

    message.answer.assert_called_once_with("hello world")

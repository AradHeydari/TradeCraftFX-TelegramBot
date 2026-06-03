"""Unit tests for keyboard builder functions."""
from __future__ import annotations

from keyboards.default.help_kb import get_help_keyboard
from keyboards.inline.start_kb import ICON_STAR, get_start_keyboard


def test_start_keyboard_left_button_has_icon() -> None:
    kb = get_start_keyboard()
    btn = kb.inline_keyboard[0][0]
    assert btn.icon_custom_emoji_id == ICON_STAR


def test_start_keyboard_right_button_no_icon() -> None:
    kb = get_start_keyboard()
    btn = kb.inline_keyboard[0][1]
    assert btn.icon_custom_emoji_id is None


def test_start_keyboard_has_two_buttons() -> None:
    kb = get_start_keyboard()
    assert len(kb.inline_keyboard[0]) == 2
    assert kb.inline_keyboard[0][0].callback_data == "demo_premium"
    assert kb.inline_keyboard[0][1].callback_data == "demo_regular"


def test_help_keyboard_has_rows() -> None:
    kb = get_help_keyboard()
    assert len(kb.keyboard) > 0


def test_help_keyboard_resize_enabled() -> None:
    kb = get_help_keyboard()
    assert kb.resize_keyboard is True

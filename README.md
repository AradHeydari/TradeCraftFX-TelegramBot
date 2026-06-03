# Aiogram 3 Bot Template

> A modern, production-ready **[aiogram 3](https://github.com/aiogram/aiogram)** Telegram bot starter template for Python — routers, type hints, `pydantic-settings`, Memory↔Redis FSM, Docker, tests, and CI. Just `git clone` and start building.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.28-blue.svg)](https://github.com/aiogram/aiogram)
[![CI](https://github.com/ulugby/aiogram3-bot-template/actions/workflows/ci.yml/badge.svg)](https://github.com/ulugby/aiogram3-bot-template/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: type hints](https://img.shields.io/badge/typed-100%25-brightgreen.svg)](https://docs.python.org/3/library/typing.html)

A clean foundation for any Telegram bot. No database, no boilerplate to delete — just the patterns you actually reuse on every project, kept up to date with the latest aiogram release.

---

## ✨ Features

- **aiogram 3.28+** — uses the modern `DefaultBotProperties` API (the new `parse_mode`)
- **Router-based** architecture — every module is an independent `Router`
- **pydantic-settings** — type-safe configuration loaded from `.env`
- **FSM storage** — Memory by default, switch to **Redis** with a single `.env` flag
- **⭐ Telegram Premium icons** — ready-to-use examples for custom emoji on **buttons and inside messages** ([see below](#-telegram-premium-icons))
- **Inline & reply keyboards** — working `/start` (inline) and `/help` (reply) examples
- **Docker + docker-compose** — bot + Redis, one command to run
- **pytest** test suite + **GitHub Actions CI**
- Logging middleware, global error handler, admin notifications, bot command menu
- **100% type-hinted**, formatted, and English throughout

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Docker](#-docker)
- [Telegram Premium Icons](#-telegram-premium-icons)
- [Configuration](#️-configuration)
- [Project Structure](#-project-structure)
- [Keyboards](#-keyboards)
- [Adding a New Handler](#-adding-a-new-handler)
- [Testing](#-testing)
- [Contributing & Contact](#-contributing--contact)
- [License](#-license)

## 🚀 Quick Start

```bash
git clone https://github.com/ulugby/aiogram3-bot-template.git
cd aiogram3-bot-template

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then put your BOT_TOKEN inside
python app.py
```

Get your `BOT_TOKEN` from [@BotFather](https://t.me/BotFather). That's it — send `/start` to your bot.

## 🐳 Docker

```bash
cp .env.example .env        # set BOT_TOKEN, and USE_REDIS=true if you want Redis
docker compose up --build
```

This starts the bot together with a Redis container for FSM storage.

## ⭐ Telegram Premium Icons

Telegram lets you show **custom emoji icons** in two places — on inline buttons and inside message text. This template ships working examples of both.

> [!IMPORTANT]
> Custom emoji icons are only rendered when the **bot owner's account has Telegram Premium**. Without Premium they are silently ignored — the button/message still works, just without the icon. No error is raised, so it's safe to ship either way.

### 1. Icon on an inline button — `icon_custom_emoji_id`

From [`keyboards/inline/start_kb.py`](keyboards/inline/start_kb.py):

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Custom emoji ID shown as a button icon (requires bot owner Telegram Premium).
ICON_STAR = "5453969572354878595"

InlineKeyboardButton(
    text="Premium user (icon enabled)",
    callback_data="demo_premium",
    icon_custom_emoji_id=ICON_STAR,   # set to None to render a plain button
)
```

### 2. Icon inside a message — `<tg-emoji>`

Because the bot uses `ParseMode.HTML`, you can drop a custom emoji straight into any text with the `<tg-emoji>` tag (see [`handlers/users/start.py`](handlers/users/start.py)):

```python
await message.answer(
    '<tg-emoji emoji-id="5453969572354878595">⭐</tg-emoji> Hello, <b>World</b>!'
)
```

The `⭐` between the tags is the **fallback** shown to non-Premium viewers; Premium users see the custom emoji.

### How do I find an emoji ID?

Send the premium/custom emoji to a helper bot such as [@idstickerbot](https://t.me/idstickerbot), or read the `custom_emoji` entity's `custom_emoji_id` from an incoming message. Replace `ICON_STAR` with your own ID.

## ⚙️ Configuration

All configuration lives in `.env` (copy it from `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Token from [@BotFather](https://t.me/BotFather) | — (required) |
| `ADMINS` | Admin Telegram IDs, comma-separated | `[]` |
| `USE_REDIS` | Use Redis for FSM storage | `false` |
| `REDIS_HOST` / `REDIS_PORT` | Redis address | `localhost` / `6379` |

## 📁 Project Structure

```
├── app.py            # entry point — assembles routers and starts polling
├── loader.py         # Bot + Dispatcher + storage factory (Memory ↔ Redis)
├── data/config.py    # type-safe Settings (pydantic-settings)
├── handlers/         # users (start/help/callbacks/echo), groups, channels, errors
├── keyboards/        # inline (premium icons) and default (reply) keyboards
├── middlewares/      # logging middleware
├── states/  utils/   # FSM states, notify_admins, set_botcommands
└── tests/            # pytest test suite
```

## ⌨️ Keyboards

### Inline keyboard (with premium icons)

`/start` shows an inline keyboard built in [`keyboards/inline/start_kb.py`](keyboards/inline/start_kb.py). It demonstrates the premium icon feature with two buttons side by side: one with `icon_custom_emoji_id` set, one without. The button taps are answered in [`handlers/users/callbacks.py`](handlers/users/callbacks.py).

### Reply keyboard

`/help` shows a reply keyboard from [`keyboards/default/help_kb.py`](keyboards/default/help_kb.py) — the classic always-visible button menu under the input field.

## ➕ Adding a New Handler

1. Create a new file in `handlers/users/`, defining a `router = Router()`.
2. Write your handler with `@router.message(...)` (or `@router.callback_query(...)`).
3. Register it in `handlers/__init__.py` inside `setup_routers()` — **before** `echo`
   (the echo handler catches all remaining text, so anything after it never runs).

```python
# handlers/users/ping.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="users:ping")


@router.message(Command("ping"))
async def ping_handler(message: Message) -> None:
    await message.answer("pong")
```

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite mocks Telegram objects, so tests run instantly with no bot token required. CI runs them on every push and pull request.

## 🤝 Contributing & Contact

Issues and pull requests are welcome! If this template helped you, a ⭐ on the repo means a lot.

Need help or have a question? Reach out on Telegram: [@ulugby](https://t.me/ulugby)

## 📄 License

Released under the [MIT License](LICENSE) — free for personal and commercial use. Do whatever you want with it; attribution is appreciated but not required.

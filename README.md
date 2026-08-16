# Telegram Subscription Bot

Telegram bot for selling subscriptions with admin panel, payment system and support.

---

## Features

- Subscription plans (1, 3, 6, 12 months)
- Payment methods: card, online gateway, cryptocurrency
- Admin panel (statistics, users, transactions, discounts, broadcast)
- Support ticket system
- Persian calendar in all outputs
- Mandatory channel membership
- Automatic expiry check and reminders
- Discount code system
- Persian user interface

---

## Technologies

- Python 3.11+
- Aiogram 3.x
- SQLite + aiosqlite
- jdatetime
- APScheduler

---

## Installation

```bash
git clone https://github.com/AradHeydari/TradeCraftFX-TelegramBot.git
cd your-repo
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env file with your bot token and settings
python app.py


## Credits

The initial project structure (folder layout and basic setup) is based on the 
[aiogram3-bot-template](https://github.com/ulugby/aiogram3-bot-template) 
created by [Ulug'bek](https://github.com/ulugby).

All bot logic, subscription system, admin panel, payment handling, and Persian localization were developed specifically for this project.
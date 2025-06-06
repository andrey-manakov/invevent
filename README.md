# 📑 Project Brief: Social Event Coordination Web App (Rev 2 – 30 May 2025)

Telegram bot for planning outings with friends.

## 1 — Purpose & Business Value

Build a lightweight web service that lets people **share upcoming-event plans**, **add friends**, and **discover & join friends’ plans**.
**Why it matters:** 65 % of Gen Z coordinate outings via ad‑hoc chat threads (Statista 2024). Centralising this flow boosts engagement for venues and users alike.

---

## 2 — Development Roadmap

## Setup

### Environment variables

Set the following variables before running the bot:

- `BOT_TOKEN` — Telegram bot token.
- `DB_URL` — database connection string (defaults to `sqlite:///db.sqlite3`).
- `ADMIN_CHAT_ID` — chat ID of the admin user.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the bot

```bash
python -m invevent.bot
```

## Features

- **Event creation wizard** — step-by-step prompts to create a new event.
- **Menus** to manage events, friends and settings.

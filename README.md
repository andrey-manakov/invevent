# InvEvent Telegram Bot

InvEvent is a small Telegram bot for planning outings with friends. It stores
events in an SQL database and lets users share, join and view them directly in
chat.

## Features

- **Event wizard** – guided steps to collect topic, event type, date/time,
  location, visibility, optional picture and description. Addresses are
  geocoded via OpenStreetMap when needed.
- **Deep links** for viewing an event description or joining it.
- **Event lists** – browse your own and joined events, your friends’ private
  events and all public events.
- **Map display** – show upcoming events on a static map or as an interactive
  HTML map; filter events that are near your current location.
- **Friends** – follow/unfollow people, view followers and who you follow and
  see friends’ events.
- **Simple settings** – delete all data or generate random demo data for
  testing.

## Configuration

Create a `.env` file or export these environment variables:

```
BOT_TOKEN=your_bot_token
DB_URL=sqlite:///db.sqlite3  # optional
ADMIN_CHAT_ID=<chat id>      # optional
```

`BOT_TOKEN` is required. `DB_URL` defaults to a local SQLite file.

## Installation

1. Install Python 3.11 or later.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The `staticmap` package is included and used for map rendering.

## Running

Start the bot with:

```bash
python -m invevent.bot
```

The bot logs to `bot.log` and sends a startup message to `ADMIN_CHAT_ID` if provided.

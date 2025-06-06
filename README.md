# InvEvent Telegram Bot

InvEvent is a small Telegram bot for planning outings with friends. It stores events in an SQL database and lets users share, join and view events directly in chat.

## Features

- **Event wizard** – guided steps to collect title, description, date/time, tag, location and visibility.
- **Deep links** for viewing an event description or joining it.
- **Event lists** – browse your events, friends' private events and all public events.
- **Map display** – show upcoming events on a single static map (uses OpenStreetMap for geocoding addresses).
- **Simple settings** – delete all events for testing.

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

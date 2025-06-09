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

## Navigation

After sending `/start` the bot shows a reply keyboard with four entries:

- **📅 Events** – open the events menu. If you have not sent your location yet
  the bot asks for it to filter nearby events from friends.
- **➕ Create event** – start the multi‑step event wizard described below.
- **👥 Friends** – manage followers/followed lists and view a friend's events.
- **⚙️ Settings** – clean up data or generate demo data.

Use the `⬅️ Back` button in each menu to return to the previous one.

### Events menu

From the events menu you can:

- list today's events from friends near your last sent location;
- view all events today or tomorrow;
- pick a friend to see just their events;
- display events on a static map.

### Friends and Settings

The friends menu lets you browse followers and who you follow. Selecting a user
shows options to unfollow, unfriend or view their upcoming events. The settings
menu currently offers two actions: delete all stored data or populate the
database with random demo data for quick testing.

## Event wizard

Choosing **Create event** launches a guided wizard. The steps are:

1. **Topic** – choose a broad topic such as sport, hobby or nature.
2. **Event type** – pick a specific activity relevant to the chosen topic.
3. **Date and time** – quickly set today or tomorrow.
4. **Location** – send GPS coordinates, pick a point on the map or type an
   address; addresses are geocoded via OpenStreetMap.
5. **Picture** – optionally attach a photo.
6. **Description** – add details and save the event. The bot replies with deep
   links for sharing the description or joining the event.

## Further documentation

Additional information about the project structure and database can be found in
the [`docs/wiki`](docs/wiki) directory which mirrors the GitHub wiki.

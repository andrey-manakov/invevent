# InvEvent Bot Overview

InvEvent is a Telegram bot that helps small groups plan outings. It stores events
in an SQL database and lets people share and join them right in chat.

Main components
---------------
* **bot.py** – entry point that configures the `TeleBot`, registers menus, the
  event wizard and callback handlers.
* **menus/** – message handlers for the main menu, events menu, friends menu and
  settings. They maintain simple per-user state via `menus/state.py`.
* **wizard/** – implements the multi-step event creation wizard. The wizard keeps
  an in-memory dictionary per user so that steps can be continued later.
* **map_view.py** – rendering of static and interactive maps with event markers
  and geocoding of addresses via OpenStreetMap.
* **models.py** – SQLAlchemy models for users, events, participation and
  friendships.

The repository includes small utilities such as `demo_data.py` for populating the
database with random events and friends.

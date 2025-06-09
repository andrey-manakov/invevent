# Bot Logic

When started, `bot.py` creates the database tables and registers all handlers.
User interaction relies on reply keyboards and a small state machine stored in
memory. The high level flow is:

1. `/start` — shows the main menu keyboard.
2. **Events** — may ask for your location, then displays today's nearby events
   from friends. The menu lets you browse all events, tomorrow's events, pick a
   friend or display a map.
3. **Create event** — launches the event wizard. Each step is handled by a
   module in `wizard/steps`:
     * topic
     * event type
     * date/time
     * location (GPS or text address)
     * optional picture
     * optional description and save
   The final message contains deep links for sharing the event description and
   joining it.
4. **Friends** — lists followers and followed users and allows unfollowing or
   viewing a friend's upcoming events.
5. **Settings** — currently lets you purge all data or populate random demo data.

The bot also supports callbacks from inline buttons, map rendering via
`map_view.py` and simple geocoding of typed addresses via OpenStreetMap.

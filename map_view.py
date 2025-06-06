from telebot import types
from .helpers import cb


def show_events_on_map(bot, chat_id: int, events):
    """Send events as map pins with a "Details" button."""
    if not events:
        bot.send_message(chat_id, "No events found.")
        return

    sent = 0
    for ev in events:
        if ev.latitude is None or ev.longitude is None:
            continue

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Details", callback_data=cb(ev.id, "details")))
        addr = ev.address or ev.location_txt or ""
        bot.send_venue(chat_id, ev.latitude, ev.longitude, ev.title, addr, reply_markup=kb)
        sent += 1

    if sent == 0:
        bot.send_message(chat_id, "No events with location to show.")

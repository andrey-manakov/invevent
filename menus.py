"""Menu handlers: My events, Friends' events, Public events"""
from telebot import types
from sqlalchemy import select
from .database import SessionLocal
from .models import Event, Participation, EventState, EventVisibility, Friendship
from .helpers import cb
from .wizard import snippet

def register_menu(bot):
    # 📅 My events
    @bot.message_handler(func=lambda m: m.text == "📅 My events")
    def my_events(msg):
        uid = msg.from_user.id
        with SessionLocal() as db:
            owned = db.scalars(select(Event)
                               .where(Event.owner_id == uid, Event.state == EventState.Active)).all()
            joined = db.scalars(select(Event)
                                .join(Participation, Participation.event_id == Event.id)
                                .where(Participation.user_id == uid, Event.state == EventState.Active)).all()
        ids = {e.id for e in owned}
        events = owned + [e for e in joined if e.id not in ids]
        if not events:
            bot.reply_to(msg, "No upcoming events."); return
        for e in events:
            kb = types.InlineKeyboardMarkup(row_width=3)
            kb.add(types.InlineKeyboardButton("Details", callback_data=cb(e.id, "details")))
            if e.owner_id == uid:
                kb.add(types.InlineKeyboardButton("Delete", callback_data=cb(e.id, "delete")))
            else:
                kb.add(types.InlineKeyboardButton("Unjoin", callback_data=cb(e.id, "unjoin")))
            bot.send_message(msg.chat.id,
                             f"<b>{e.title}</b> — {e.datetime_utc:%Y-%m-%d %H:%M UTC}\n{snippet(e.description,120)}",
                             parse_mode="HTML", reply_markup=kb)

    # 🧑‍🤝‍🧑 Friends' events
    @bot.message_handler(func=lambda m: m.text == "🧑‍🤝‍🧑 Friends' events")
    def friends_events(msg):
        uid = msg.from_user.id
        with SessionLocal() as db:
            followees = db.scalars(select(Friendship.followee_id)
                                   .where(Friendship.follower_id == uid)).all()
            events = db.scalars(select(Event)
                                .where(Event.owner_id.in_(followees),
                                       Event.state == EventState.Active)).all()
        if not events:
            bot.reply_to(msg, "Friends haven't posted events."); return
        for e in events:
            kb = types.InlineKeyboardMarkup(row_width=3)
            kb.add(types.InlineKeyboardButton("Details", callback_data=cb(e.id, "details")),
                   types.InlineKeyboardButton("Join", callback_data=cb(e.id, "join")))
            bot.send_message(msg.chat.id,
                             f"<b>{e.title}</b> — {e.datetime_utc:%Y-%m-%d %H:%M UTC}",
                             parse_mode="HTML", reply_markup=kb)

    # 🌐 Public events
    @bot.message_handler(func=lambda m: m.text == "🌐 Public events")
    def public_events(msg):
        with SessionLocal() as db:
            events = db.scalars(select(Event)
                                .where(Event.visibility == EventVisibility.Public,
                                       Event.state == EventState.Active)).all()
        if not events:
            bot.reply_to(msg, "No public events yet."); return
        for e in events:
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("Details", callback_data=cb(e.id, "details")),
                   types.InlineKeyboardButton("Join", callback_data=cb(e.id, "join")))
            bot.send_message(msg.chat.id,
                             f"<b>{e.title}</b> — {e.datetime_utc:%Y-%m-%d %H:%M UTC}",
                             parse_mode="HTML", reply_markup=kb)
    
    # ⚙️ Settings → open a small submenu
    @bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
    def settings_menu(msg):
        SETTINGS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        SETTINGS_KB.add("🗑️ Delete events", "⬅️ Back")
        bot.send_message(msg.chat.id, "Settings:", reply_markup=SETTINGS_KB)

    # 🗑️ Delete all events from the database
    @bot.message_handler(func=lambda m: m.text == "🗑️ Delete events")
    def delete_events(msg):
        with SessionLocal() as db:
            # remove all Participation rows first (FK constraints), then all Event rows
            db.query(Participation).delete()
            db.query(Event).delete()
            db.commit()
        bot.reply_to(msg, "All events have been deleted.")

    # ⬅️ Back → return to main menu
    @bot.message_handler(func=lambda m: m.text == "⬅️ Back")
    def back_to_main(msg):
        # lazy‐import MAIN_KB here to avoid circular import
        from .bot import MAIN_KB
        bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)

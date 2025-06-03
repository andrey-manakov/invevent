"""Menu handlers: My events, Friends' events, Public events"""
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from .database import SessionLocal
from .models import Event, Participation, EventState, EventVisibility, Friendship, User
from .helpers import cb
from .wizard import snippet

def register_menu(bot):
    print("starting regidtering the menu commands")
    @bot.message_handler(commands=['start'])
    def handle_start_cmd(msg):
        print("starting registering logic for start command")
        parts = msg.text.split(maxsplit=1)
        print("splitting to parts {parts}")
        if len(parts) < 2:
            return  # no parameter

        param = parts[1]
        user_id = msg.from_user.id

        # Helper: make two-way friendship
        def make_friends(u1, u2):
            with SessionLocal() as db:
                if not db.get(Friendship, {"follower_id": u1, "followee_id": u2}):
                    db.add(Friendship(follower_id=u1, followee_id=u2))
                if not db.get(Friendship, {"follower_id": u2, "followee_id": u1}):
                    db.add(Friendship(follower_id=u2, followee_id=u1))
                db.commit()

        if param.startswith("desc_"):
            eid = param[5:]
            with SessionLocal() as db:
                ev = db.get(Event, eid)
                if not ev or ev.state != EventState.Active:
                    bot.send_message(user_id, "Event not found or not active.")
                    return
                make_friends(user_id, ev.owner_id)

                part = db.get(Participation, {"event_id": eid, "user_id": user_id})
                inline_kb = InlineKeyboardMarkup()
                if part:
                    inline_kb.add(InlineKeyboardButton("Unjoin", callback_data=cb(eid, "unjoin")))
                else:
                    inline_kb.add(InlineKeyboardButton("Join", callback_data=cb(eid, "join")))

                text = (
                    f"<b>{ev.title}</b>\n"
                    f"{ev.description}\n\n"
                    f"🗓️ {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n"
                    f"📍 {ev.location_txt}\n"
                    f"🔒 {'Private' if ev.visibility == EventVisibility.Private else 'Public'}"
                )
                bot.send_message(user_id, text, parse_mode="HTML", reply_markup=inline_kb)
            return

        if param.startswith("join_"):
            eid = param[5:]
            with SessionLocal() as db:
                ev = db.get(Event, eid)
                if not ev or ev.state != EventState.Active:
                    bot.send_message(user_id, "Event not found or not active.")
                    return
                make_friends(user_id, ev.owner_id)

                if not db.get(Participation, {"event_id": eid, "user_id": user_id}):
                    db.add(Participation(event_id=eid, user_id=user_id))
                    db.commit()

                inline_kb = InlineKeyboardMarkup()
                inline_kb.add(InlineKeyboardButton("Unjoin", callback_data=cb(eid, "unjoin")))

                text = (
                    f"<b>{ev.title}</b>\n"
                    f"{ev.description}\n\n"
                    f"🗓️ {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n"
                    f"📍 {ev.location_txt}\n"
                    f"🔒 {'Private' if ev.visibility == EventVisibility.Private else 'Public'}\n"
                    f"✅ You have joined this event."
                )
                bot.send_message(user_id, text, parse_mode="HTML", reply_markup=inline_kb)
            return

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

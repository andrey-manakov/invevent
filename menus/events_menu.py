from datetime import datetime, timezone
from telebot import types
from sqlalchemy import select
from ..database import SessionLocal
from ..models import Event, Participation, EventState, EventVisibility, Friendship
from ..helpers import cb
from .state import set_state, get_state

EVENTS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
EVENTS_KB.add("\ud83d\udccb My events", "\ud83e\udefc Friends events", "\ud83c\udf10 Public events", "\u2b05\ufe0f Back")

LIST_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LIST_KB.add("\ud83d\udccd Show on map", "\u2b05\ufe0f Back")


def _list_events(user_id, events):
    text_lines = []
    kb = types.InlineKeyboardMarkup()
    for e in events:
        text_lines.append(f"\u2022 {e.title} \u2014 {e.datetime_utc:%d %b}")
        kb.add(types.InlineKeyboardButton(e.title, callback_data=cb(e.id, "summary")))
    if not text_lines:
        text_lines.append("(none)")
    return "\n".join(text_lines), kb


def _friends_events(uid):
    with SessionLocal() as db:
        followees = db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()
        events = db.scalars(select(Event).where(Event.owner_id.in_(followees), Event.state == EventState.Active, Event.visibility == EventVisibility.Private)).all()
    return events


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "\ud83d\udcc5 Events")
    def events_main(msg):
        print(msg)
        uid = msg.from_user.id
        set_state(uid, "events")
        events = _friends_events(uid)
        text, ikb = _list_events(uid, events)
        bot.send_message(msg.chat.id, text, reply_markup=ikb)
        bot.send_message(msg.chat.id, "Select:", reply_markup=EVENTS_KB)

    @bot.message_handler(func=lambda m: m.text == "\ud83d\udccb My events")
    def my_events(msg):
        uid = msg.from_user.id
        set_state(uid, "my_events")
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            owned = db.scalars(select(Event).where(Event.owner_id == uid, Event.state == EventState.Active, Event.datetime_utc >= today)).all()
            joined = db.scalars(select(Event).join(Participation, Participation.event_id == Event.id).where(Participation.user_id == uid, Event.state == EventState.Active, Event.datetime_utc >= today)).all()
        text_o, kb_o = _list_events(uid, owned)
        bot.send_message(msg.chat.id, "<b>Your events:</b>\n" + text_o, parse_mode="HTML", reply_markup=kb_o)
        others = [e for e in joined if e.owner_id != uid]
        text_j, kb_j = _list_events(uid, others)
        bot.send_message(msg.chat.id, "<b>Joined:</b>\n" + text_j, parse_mode="HTML", reply_markup=kb_j)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "\ud83e\udefc Friends events")
    def friends_events(msg):
        uid = msg.from_user.id
        set_state(uid, "friends_events")
        events = _friends_events(uid)
        text, ikb = _list_events(uid, events)
        bot.send_message(msg.chat.id, text, reply_markup=ikb)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "\ud83c\udf10 Public events")
    def public_events(msg):
        uid = msg.from_user.id
        set_state(uid, "public_events")
        with SessionLocal() as db:
            events = db.scalars(select(Event).where(Event.visibility == EventVisibility.Public, Event.state == EventState.Active)).all()
        text, ikb = _list_events(uid, events)
        bot.send_message(msg.chat.id, text, reply_markup=ikb)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "\ud83d\udccd Show on map")
    def show_on_map(msg):
        bot.reply_to(msg, "Map view is not implemented yet.")

    @bot.message_handler(func=lambda m: m.text == "\u2b05\ufe0f Back")
    def back(msg):
        uid = msg.from_user.id
        state = get_state(uid)
        if state in ("my_events", "friends_events", "public_events"):
            set_state(uid, "events")
            bot.send_message(msg.chat.id, "Events:", reply_markup=EVENTS_KB)
        else:
            from ..bot import MAIN_KB
            set_state(uid, "main")
            bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)


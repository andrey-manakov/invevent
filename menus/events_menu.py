from datetime import datetime, timezone
from telebot import types
from sqlalchemy import select
from ..database import SessionLocal
from ..models import Event, Participation, EventState, EventVisibility, Friendship
from ..helpers import cb
from .state import set_state, get_state
import logging

log = logging.getLogger(__name__)

EVENTS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
EVENTS_KB.add("📋 My events", "👥 Friends events", "🌐 Public events", "⬅️ Back")

LIST_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LIST_KB.add("📍 Show on map", "⬅️ Back")


def _list_events(user_id, events):
    """Return text/kb pair for event list with button-only style."""

    kb = types.InlineKeyboardMarkup()
    for e in events:
        label = f"{e.title} — {e.datetime_utc:%d %b}"
        kb.add(types.InlineKeyboardButton(label, callback_data=cb(e.id, "summary")))

    if events:
        return "", kb
    return "(none)", None


def _friends_events(uid):
    with SessionLocal() as db:
        followees = db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()
        events = db.scalars(select(Event).where(Event.owner_id.in_(followees), Event.state == EventState.Active, Event.visibility == EventVisibility.Private)).all()
    return events


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "📅 Events")
    def events_main(msg):
        uid = msg.from_user.id
        set_state(uid, "events")
        events = _friends_events(uid)
        text, ikb = _list_events(uid, events)

        header = "<b>Friends events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=ikb)
        bot.send_message(msg.chat.id, "Select:", reply_markup=EVENTS_KB)

    @bot.message_handler(func=lambda m: m.text == "📋 My events")
    def my_events(msg):
        log.debug("my events handling")
        uid = msg.from_user.id
        set_state(uid, "my_events")
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            owned = db.scalars(select(Event).where(Event.owner_id == uid, Event.state == EventState.Active, Event.datetime_utc >= today)).all()
            joined = db.scalars(select(Event).join(Participation, Participation.event_id == Event.id).where(Participation.user_id == uid, Event.state == EventState.Active, Event.datetime_utc >= today)).all()
        text_o, kb_o = _list_events(uid, owned)
        header_o = "<b>Your events:</b>"
        if text_o:
            header_o += "\n" + text_o
        bot.send_message(msg.chat.id, header_o, parse_mode="HTML", reply_markup=kb_o)
        others = [e for e in joined if e.owner_id != uid]
        text_j, kb_j = _list_events(uid, others)
        header_j = "<b>Joined:</b>"
        if text_j:
            header_j += "\n" + text_j
        bot.send_message(msg.chat.id, header_j, parse_mode="HTML", reply_markup=kb_j)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "👥 Friends events")
    def friends_events(msg):
        uid = msg.from_user.id
        set_state(uid, "friends_events")
        events = _friends_events(uid)
        text, ikb = _list_events(uid, events)
        header = "<b>Friends events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=ikb)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "🌐 Public events")
    def public_events(msg):
        uid = msg.from_user.id
        set_state(uid, "public_events")
        with SessionLocal() as db:
            events = db.scalars(select(Event).where(Event.visibility == EventVisibility.Public, Event.state == EventState.Active)).all()
        text, ikb = _list_events(uid, events)
        header = "<b>Public events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=ikb)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "📍 Show on map")
    def show_on_map(msg):
        uid = msg.from_user.id
        state = get_state(uid)

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        if state == "my_events":
            with SessionLocal() as db:
                owned = db.scalars(select(Event).where(Event.owner_id == uid,
                                                    Event.state == EventState.Active,
                                                    Event.datetime_utc >= today)).all()
                joined = db.scalars(select(Event).join(Participation, Participation.event_id == Event.id)
                                   .where(Participation.user_id == uid,
                                          Event.state == EventState.Active,
                                          Event.datetime_utc >= today)).all()
            events = owned + [e for e in joined if e.owner_id != uid]
        elif state == "friends_events":
            events = _friends_events(uid)
        elif state == "public_events":
            with SessionLocal() as db:
                events = db.scalars(select(Event)
                                   .where(Event.visibility == EventVisibility.Public,
                                          Event.state == EventState.Active)).all()
        else:
            bot.reply_to(msg, "Please select a list first.")
            return

        from ..map_view import show_events_interactive_map
        show_events_interactive_map(bot, msg.chat.id, events)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Back")
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


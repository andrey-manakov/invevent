from datetime import datetime, timezone, timedelta
from telebot import types
from telebot.handler_backends import ContinueHandling
from sqlalchemy import select

from ..database import SessionLocal
from ..models import Event, Participation, EventState, Friendship, User
from ..helpers import cb
from ..map_view import show_events_on_map, filter_nearby_events
from .state import set_state, get_state

import logging

log = logging.getLogger(__name__)

# ──────────────────────────── keyboards ─────────────────────────────
EVENTS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
EVENTS_KB.add("All", "Tomorrow", "Friend's events", "Location", "⬅️ Back")

LOC_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
LOC_KB.add(types.KeyboardButton("📍 Send my current location", request_location=True))
LOC_KB.add("⬅️ Back")

LIST_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LIST_KB.add("📍 Show on map", "📍 Nearby")
LIST_KB.add("⬅️ Back")

# store last known location per user
LAST_LOCATION = {}


def _today_range(offset: int = 0):
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=offset)
    end = start + timedelta(days=1)
    return start, end


def _list_events(events, *, show_owner: bool = False):
    kb = types.InlineKeyboardMarkup()
    owner_names = {}
    if show_owner:
        with SessionLocal() as db:
            ids = {e.owner_id for e in events}
            if ids:
                rows = db.execute(select(User.id, User.first_name).where(User.id.in_(ids))).all()
                owner_names = {uid: name for uid, name in rows}
    for e in events:
        title = e.title
        if title.lower() == "other" and e.tags:
            title = e.tags.split(",")[0]
        parts = []
        if show_owner:
            parts.append(owner_names.get(e.owner_id, str(e.owner_id)))
        parts.append(title)
        label = f"{' '.join(parts)} — {e.datetime_utc:%d %b}"
        kb.add(types.InlineKeyboardButton(label, callback_data=cb(e.id, "summary")))
    if events:
        return "", kb
    return "(none)", None


def _friend_ids(uid: int):
    with SessionLocal() as db:
        return db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()


def _friends_events_today(uid: int):
    start, end = _today_range()
    ids = _friend_ids(uid)
    if not ids:
        return []
    with SessionLocal() as db:
        return db.scalars(
            select(Event).where(
                Event.owner_id.in_(ids),
                Event.state == EventState.Active,
                Event.datetime_utc >= start,
                Event.datetime_utc < end,
            )
        ).all()


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "📅 Events")
    def events_main(msg):
        uid = msg.from_user.id
        if uid not in LAST_LOCATION:
            set_state(uid, "await_location")
            bot.send_message(msg.chat.id, "Send your location to see today's events from friends:", reply_markup=LOC_KB)
            return
        set_state(uid, "events")
        lat, lon = LAST_LOCATION[uid]
        events = _friends_events_today(uid)
        events = filter_nearby_events(events, lat, lon)
        text, kb = _list_events(events, show_owner=True)
        header = "<b>Today's nearby events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=kb)
        bot.send_message(msg.chat.id, "Menu:", reply_markup=EVENTS_KB)

    @bot.message_handler(content_types=["location"])
    def save_location(msg):
        uid = msg.from_user.id
        if get_state(uid) != "await_location":
            return ContinueHandling()
        LAST_LOCATION[uid] = (msg.location.latitude, msg.location.longitude)
        set_state(uid, "events")
        events = _friends_events_today(uid)
        events = filter_nearby_events(events, msg.location.latitude, msg.location.longitude)
        text, kb = _list_events(events, show_owner=True)
        header = "<b>Today's nearby events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=kb)
        bot.send_message(msg.chat.id, "Menu:", reply_markup=EVENTS_KB)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "events" and m.text == "All")
    def all_today(msg):
        start, end = _today_range()
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.state == EventState.Active,
                    Event.datetime_utc >= start,
                    Event.datetime_utc < end,
                )
            ).all()
        text, kb = _list_events(events, show_owner=True)
        header = "<b>All events today:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "events" and m.text == "Tomorrow")
    def all_tomorrow(msg):
        start, end = _today_range(1)
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.state == EventState.Active,
                    Event.datetime_utc >= start,
                    Event.datetime_utc < end,
                )
            ).all()
        text, kb = _list_events(events, show_owner=True)
        header = "<b>Events tomorrow:</b>"
        if text:
            header += "\n" + text
        bot.send_message(msg.chat.id, header, parse_mode="HTML", reply_markup=kb)

    SELECT_CTX = {}

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "events" and m.text == "Friend's events")
    def choose_friend(msg):
        uid = msg.from_user.id
        with SessionLocal() as db:
            ids = _friend_ids(uid)
            users = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
        if not users:
            bot.reply_to(msg, "No friends found.")
            return
        kb = types.InlineKeyboardMarkup()
        for u in users:
            kb.add(types.InlineKeyboardButton(u.first_name, callback_data=f"frsel:{u.id}"))
        SELECT_CTX[uid] = True
        bot.send_message(msg.chat.id, "Choose friend:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("frsel:"))
    def show_friend(c):
        uid = c.from_user.id
        fid = int(c.data.split(":", 1)[1])
        start, end = _today_range()
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.owner_id == fid,
                    Event.state == EventState.Active,
                    Event.datetime_utc >= start,
                    Event.datetime_utc < end,
                )
            ).all()
        text, kb = _list_events(events)
        header = "<b>Friend's events today:</b>"
        if text:
            header += "\n" + text
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, header, parse_mode="HTML", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "events" and m.text == "Location")
    def show_map(msg):
        uid = msg.from_user.id
        if uid not in LAST_LOCATION:
            bot.reply_to(msg, "No location set.")
            return
        lat, lon = LAST_LOCATION[uid]
        events = _friends_events_today(uid)
        events = filter_nearby_events(events, lat, lon)
        show_events_on_map(bot, msg.chat.id, events)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Back")
    def back(msg):
        from ..bot import MAIN_KB
        set_state(msg.from_user.id, "main")
        bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)

from datetime import datetime, timezone, timedelta
from telebot import types
from telebot.handler_backends import ContinueHandling
from sqlalchemy import select
from ..database import SessionLocal
from ..models import Event, Participation, EventState, EventVisibility, Friendship, User
from ..helpers import cb
from .state import set_state, get_state
import logging

log = logging.getLogger(__name__)

EVENTS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
EVENTS_KB.add("📋 My events", "👥 Friends events", "🌐 Public events", "⬅️ Back")

LIST_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LIST_KB.add("📍 Show on map", "🔍 Filter", "📍 Nearby", "⬅️ Back")

# filter menu keyboard
FILTER_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
FILTER_KB.add("👤 By friend", "Today", "Tomorrow", "📅 Date", "🎯 Type", "Reset filters", "⬅️ Back")

# store which list the user was viewing when requesting nearby events
NEARBY_CTX = {}

# store active filters per user
FILTERS = {}
# remember which list was open when entering filter menu
FILTER_ORIGIN = {}


def _list_events(user_id, events, *, show_owner: bool = False):
    """Return text/kb pair for event list with button-only style."""

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


def _friends_events(uid):
    with SessionLocal() as db:
        followees = db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()
        events = db.scalars(select(Event).where(Event.owner_id.in_(followees), Event.state == EventState.Active, Event.visibility == EventVisibility.Private)).all()
    return events


def _events_for_state(uid: int, state: str):
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
        return owned + [e for e in joined if e.owner_id != uid]
    elif state == "friends_events":
        return _friends_events(uid)
    elif state == "public_events":
        with SessionLocal() as db:
            return db.scalars(select(Event)
                              .where(Event.visibility == EventVisibility.Public,
                                     Event.state == EventState.Active)).all()
    return []


def _apply_filters(events, uid: int):
    f = FILTERS.get(uid, {})
    res = events
    if f.get("friend"):
        res = [e for e in res if e.owner_id == f["friend"]]
    if "date" in f:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if f["date"] == "today":
            start = today
            end = start + timedelta(days=1)
        elif f["date"] == "tomorrow":
            start = today + timedelta(days=1)
            end = start + timedelta(days=1)
        else:
            d = f["date"]
            start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            end = start + timedelta(days=1)
        res = [e for e in res if start <= e.datetime_utc < end]
    if f.get("type"):
        tag = f["type"]
        res = [e for e in res if tag in e.tags]
    return res


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "📅 Events")
    def events_main(msg):
        uid = msg.from_user.id
        set_state(uid, "events")
        bot.send_message(msg.chat.id, "Events:", reply_markup=EVENTS_KB)

    @bot.message_handler(func=lambda m: m.text == "📋 My events")
    def my_events(msg):
        log.debug("my events handling")
        uid = msg.from_user.id
        set_state(uid, "my_events")
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            owned = db.scalars(select(Event).where(Event.owner_id == uid,
                                                   Event.state == EventState.Active,
                                                   Event.datetime_utc >= today)).all()
            joined = db.scalars(select(Event).join(Participation, Participation.event_id == Event.id)
                               .where(Participation.user_id == uid,
                                      Event.state == EventState.Active,
                                      Event.datetime_utc >= today)).all()
        owned = _apply_filters(owned, uid)
        joined = _apply_filters([e for e in joined if e.owner_id != uid], uid)
        text_o, kb_o = _list_events(uid, owned)
        header_o = "<b>Your events:</b>"
        if text_o:
            header_o += "\n" + text_o
        bot.send_message(msg.chat.id, header_o, parse_mode="HTML", reply_markup=kb_o)
        text_j, kb_j = _list_events(uid, joined)
        header_j = "<b>Joined:</b>"
        if text_j:
            header_j += "\n" + text_j
        bot.send_message(msg.chat.id, header_j, parse_mode="HTML", reply_markup=kb_j)
        bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "👥 Friends events")
    def friends_events(msg):
        uid = msg.from_user.id
        set_state(uid, "friends_events")
        events = _apply_filters(_friends_events(uid), uid)
        text, ikb = _list_events(uid, events, show_owner=True)
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
            events = db.scalars(select(Event).where(Event.visibility == EventVisibility.Public,
                                                   Event.state == EventState.Active)).all()
        events = _apply_filters(events, uid)
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

        if state not in ("my_events", "friends_events", "public_events"):
            bot.reply_to(msg, "Please select a list first.")
            return
        events = _apply_filters(_events_for_state(uid, state), uid)

        from ..map_view import show_events_on_map
        show_events_on_map(bot, msg.chat.id, events)

    @bot.message_handler(func=lambda m: m.text == "🔍 Filter")
    def filter_menu(msg):
        uid = msg.from_user.id
        state = get_state(uid)
        if state not in ("my_events", "friends_events", "public_events"):
            return
        FILTER_ORIGIN[uid] = state
        set_state(uid, "filter_menu")
        bot.send_message(msg.chat.id, "Select filters:", reply_markup=FILTER_KB)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_menu" and m.text == "Reset filters")
    def reset_filters(msg):
        FILTERS.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Filters reset")
        show_filtered(msg.from_user.id, msg.chat.id)

    def show_filtered(uid: int, chat_id: int):
        origin = FILTER_ORIGIN.get(uid, "events")
        if origin == "my_events":
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            with SessionLocal() as db:
                owned = db.scalars(select(Event).where(Event.owner_id == uid,
                                                       Event.state == EventState.Active,
                                                       Event.datetime_utc >= today)).all()
                joined = db.scalars(select(Event).join(Participation, Participation.event_id == Event.id)
                                   .where(Participation.user_id == uid,
                                          Event.state == EventState.Active,
                                          Event.datetime_utc >= today)).all()
            owned = _apply_filters(owned, uid)
            joined = _apply_filters([e for e in joined if e.owner_id != uid], uid)
            text_o, kb_o = _list_events(uid, owned)
            header_o = "<b>Your events:</b>"
            if text_o:
                header_o += "\n" + text_o
            bot.send_message(chat_id, header_o, parse_mode="HTML", reply_markup=kb_o)
            text_j, kb_j = _list_events(uid, joined)
            header_j = "<b>Joined:</b>"
            if text_j:
                header_j += "\n" + text_j
            bot.send_message(chat_id, header_j, parse_mode="HTML", reply_markup=kb_j)
        elif origin == "friends_events":
            events = _apply_filters(_friends_events(uid), uid)
            text, kb = _list_events(uid, events, show_owner=True)
            header = "<b>Friends events:</b>"
            if text:
                header += "\n" + text
            bot.send_message(chat_id, header, parse_mode="HTML", reply_markup=kb)
        elif origin == "public_events":
            with SessionLocal() as db:
                events = db.scalars(select(Event).where(Event.visibility == EventVisibility.Public,
                                                       Event.state == EventState.Active)).all()
            events = _apply_filters(events, uid)
            text, kb = _list_events(uid, events)
            header = "<b>Public events:</b>"
            if text:
                header += "\n" + text
            bot.send_message(chat_id, header, parse_mode="HTML", reply_markup=kb)
        bot.send_message(chat_id, "Options:", reply_markup=FILTER_KB)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_menu" and m.text in ("Today", "Tomorrow"))
    def date_shortcuts(msg):
        uid = msg.from_user.id
        f = FILTERS.setdefault(uid, {})
        f["date"] = msg.text.lower()
        show_filtered(uid, msg.chat.id)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_menu" and m.text == "📅 Date")
    def date_prompt(msg):
        set_state(msg.from_user.id, "filter_date")
        bot.send_message(msg.chat.id, "Send date YYYY-MM-DD:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_date")
    def set_date(msg):
        try:
            d = datetime.strptime(msg.text, "%Y-%m-%d").date()
        except ValueError:
            bot.reply_to(msg, "Invalid date")
            return
        uid = msg.from_user.id
        f = FILTERS.setdefault(uid, {})
        f["date"] = d
        set_state(uid, "filter_menu")
        show_filtered(uid, msg.chat.id)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_menu" and m.text == "🎯 Type")
    def type_prompt(msg):
        kb = types.InlineKeyboardMarkup()
        from ..wizard.wizard_utils import TOPICS
        for t in TOPICS:
            kb.add(types.InlineKeyboardButton(t, callback_data=f"ftype:{t}"))
        bot.send_message(msg.chat.id, "Select type:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ftype:"))
    def set_type(c):
        uid = c.from_user.id
        f = FILTERS.setdefault(uid, {})
        f["type"] = c.data.split(":", 1)[1]
        bot.answer_callback_query(c.id)
        show_filtered(uid, c.message.chat.id)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_menu" and m.text == "👤 By friend")
    def friend_prompt(msg):
        uid = msg.from_user.id
        with SessionLocal() as db:
            ids = db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()
            users = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
        kb = types.InlineKeyboardMarkup()
        for u in users:
            kb.add(types.InlineKeyboardButton(u.first_name, callback_data=f"ffriend:{u.id}"))
        bot.send_message(msg.chat.id, "Choose friend:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ffriend:"))
    def set_friend(c):
        uid = c.from_user.id
        fid = int(c.data.split(":", 1)[1])
        FILTERS.setdefault(uid, {})["friend"] = fid
        bot.answer_callback_query(c.id)
        show_filtered(uid, c.message.chat.id)

    @bot.message_handler(func=lambda m: m.text == "📍 Nearby")
    def nearby_request(msg):
        uid = msg.from_user.id
        state = get_state(uid)
        if state not in ("my_events", "friends_events", "public_events"):
            bot.reply_to(msg, "Please select a list first.")
            return

        NEARBY_CTX[uid] = state
        set_state(uid, "nearby_wait")

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
        kb.add("⬅️ Back")
        bot.send_message(msg.chat.id, "Send your location to see nearby events:", reply_markup=kb)

    @bot.message_handler(content_types=["location"])
    def handle_nearby_location(msg):
        uid = msg.from_user.id
        if get_state(uid) != "nearby_wait":
            return ContinueHandling()

        prev = NEARBY_CTX.pop(uid, None)
        set_state(uid, prev or "events")

        user_lat = msg.location.latitude
        user_lon = msg.location.longitude

        if prev not in ("my_events", "friends_events", "public_events"):
            bot.reply_to(msg, "Please select a list first.")
            return

        events = _apply_filters(_events_for_state(uid, prev), uid)

        from ..map_view import show_events_on_map, filter_nearby_events
        nearby = filter_nearby_events(events, user_lat, user_lon)
        show_events_on_map(bot, msg.chat.id, nearby)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Back")
    def back(msg):
        uid = msg.from_user.id
        state = get_state(uid)
        if state == "nearby_wait":
            prev = NEARBY_CTX.pop(uid, None)
            set_state(uid, prev or "events")
            bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)
        elif state in ("my_events", "friends_events", "public_events"):
            set_state(uid, "events")
            bot.send_message(msg.chat.id, "Events:", reply_markup=EVENTS_KB)
        elif state in ("filter_menu", "filter_date"):
            origin = FILTER_ORIGIN.get(uid, "events")
            set_state(uid, origin)
            bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)
        else:
            from ..bot import MAIN_KB
            set_state(uid, "main")
            bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)


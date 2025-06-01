# == standard library ==
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

# == third‑party ==
from dotenv import load_dotenv
from sqlalchemy import (
    Column, String, Integer, DateTime, Enum, ForeignKey, create_engine,
    select, func, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
import telebot
from telebot import types

# ──────────────────────────────────────────────────────────────
# 1. Config / Setup
# ──────────────────────────────────────────────────────────────

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DB_URL: str = os.getenv("DB_URL", "sqlite:///db.sqlite3")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env file")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)
log = logging.getLogger("invevent")

# Database
engine = create_engine(DB_URL, echo=False, future=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

# ──────────────────────────────────────────────────────────────
# 2. Data Models (PoC schema)
# ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # TG user id
    first_name: Mapped[str] = mapped_column(String(64))
    username: Mapped[Optional[str]] = mapped_column(String(64))

    def __repr__(self):
        return f"<User {self.id} @{self.username}>"


class EventVisibility(str, Enum):
    Public = "Public"
    Friends = "Friends"


class EventState(str, Enum):
    Active = "Active"
    Past = "Past"
    Deleted = "Deleted"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID4 str
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    datetime_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_txt: Mapped[str] = mapped_column(String(120))
    visibility: Mapped[EventVisibility] = mapped_column(Enum(EventVisibility))
    tags: Mapped[str] = mapped_column(String(120))  # CSV within PoC
    notification_offset_min: Mapped[Optional[int]] = mapped_column(Integer)
    state: Mapped[EventState] = mapped_column(Enum(EventState), default=EventState.Active)


class Participation(Base):
    __tablename__ = "participations"

    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())


class Friendship(Base):
    __tablename__ = "friendships"

    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    followee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())

# Create tables if first run
Base.metadata.create_all(engine)

# ──────────────────────────────────────────────────────────────
# 3. Bot & Keyboards
# ──────────────────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

PERSISTENT_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
PERSISTENT_KB.add(
    "📅 My events", "🧑‍🤝‍🧑 Friends' events",
    "🌐 Public events", "➕ Create event",
    "⚙️ Settings"
)

TAG_CATALOGUE: List[str] = [
    "🎉 Party", "🎮 Gaming", "🍽️ Food", "🎬 Cinema", "🏞️ Outdoor", "🎵 Concert", "🛍️ Shopping"
]

# Helper: build callback payload
def cb(event_id: str, verb: str) -> str:
    return f"evt:{event_id}:act:{verb}"

# Helper: truncate and escape description for list view
MAX_DESC_SNIPPET = 50

def snippet(text: str, max_len: int = MAX_DESC_SNIPPET) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"

# ──────────────────────────────────────────────────────────────
# 4. Command & Message Handlers
# ──────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(msg: types.Message):
    with SessionLocal() as db:
        ensure_user(db, msg.from_user)
    bot.send_message(
        msg.chat.id,
        "<b>Hi {}</b>! I can help you plan and share events.\nChoose an option ↓".format(msg.from_user.first_name),
        reply_markup=PERSISTENT_KB
    )


def ensure_user(db, tg_user: types.User):
    u = db.get(User, tg_user.id)
    if not u:
        u = User(id=tg_user.id, first_name=tg_user.first_name, username=tg_user.username)
        db.add(u)
        db.commit()
    else:
        # Update username changes
        if u.username != tg_user.username:
            u.username = tg_user.username
            db.commit()

# == My events ==
@bot.message_handler(func=lambda m: m.text == "📅 My events")
def handle_my_events(msg: types.Message):
    user_id = msg.from_user.id
    with SessionLocal() as db:
        events = db.scalars(
            select(Event)
            .where(
                (Event.owner_id == user_id) |
                (Event.id.in_(select(Participation.event_id).where(Participation.user_id == user_id)))
            )
            .where(Event.state == EventState.Active)
            .order_by(Event.datetime_utc)
            .limit(5)  # TODO pagination
        ).all()

    if not events:
        bot.reply_to(msg, "You have no upcoming events.")
        return

    for ev in events:
        text = f"<b>{ev.title}</b> — {ev.datetime_utc.strftime('%Y‑%m‑%d %H:%M UTC')}\n{snippet(ev.description)}"
        buttons = types.InlineKeyboardMarkup(row_width=3)
        buttons.add(
            types.InlineKeyboardButton("Details", callback_data=cb(ev.id, "details")),
            types.InlineKeyboardButton("Edit", callback_data=cb(ev.id, "edit")),
            types.InlineKeyboardButton("Delete" if ev.owner_id == user_id else "Leave", callback_data=cb(ev.id, "delete")),
        )
        bot.send_message(msg.chat.id, text, reply_markup=buttons)

# == Friends' events ==
@bot.message_handler(func=lambda m: m.text == "🧑‍🤝‍🧑 Friends' events")
def handle_friends_events(msg: types.Message):
    user_id = msg.from_user.id

    with SessionLocal() as db:
        friend_ids = db.scalars(
            select(Friendship.followee_id).where(Friendship.follower_id == user_id)
        ).all()
        if not friend_ids:
            bot.reply_to(msg, "You are not following anyone yet. Join an event through a deeplink first!")
            return

        events = db.scalars(
            select(Event)
            .where(Event.owner_id.in_(friend_ids))
            .where(Event.state == EventState.Active)
            .order_by(Event.datetime_utc)
            .limit(5)  # TODO pagination
        ).all()

    if not events:
        bot.reply_to(msg, "No upcoming events from your friends.")
        return

    for ev in events:
        joined = "✔️ Joined" if user_joined_event(user_id, ev.id) else "Join"
        text = f"<b>{ev.title}</b> — {ev.datetime_utc.strftime('%Y‑%m‑%d %H:%M UTC')}\n{snippet(ev.description)}"
        buttons = types.InlineKeyboardMarkup(row_width=3)
        buttons.add(
            types.InlineKeyboardButton("Details", callback_data=cb(ev.id, "details")),
            types.InlineKeyboardButton(joined, callback_data=cb(ev.id, "join")),
            types.InlineKeyboardButton("Unfriend", callback_data=cb(ev.id, "unfriend")),
        )
        bot.send_message(msg.chat.id, text, reply_markup=buttons)


# == Public events ==
@bot.message_handler(func=lambda m: m.text == "🌐 Public events")
def handle_public_events(msg: types.Message):
    user_id = msg.from_user.id
    with SessionLocal() as db:
        events = db.scalars(
            select(Event)
            .where(Event.visibility == EventVisibility.Public)
            .where(Event.state == EventState.Active)
            .order_by(Event.datetime_utc)
            .limit(5)
        ).all()

    if not events:
        bot.reply_to(msg, "No public events right now.")
        return

    for ev in events:
        joined = "✔️ Joined" if user_joined_event(user_id, ev.id) else "Join"
        text = f"<b>{ev.title}</b> — {ev.datetime_utc.strftime('%Y‑%m‑%d %H:%M UTC')}\n{snippet(ev.description)}"
        buttons = types.InlineKeyboardMarkup(row_width=2)
        buttons.add(
            types.InlineKeyboardButton("Details", callback_data=cb(ev.id, "details")),
            types.InlineKeyboardButton(joined, callback_data=cb(ev.id, "join")),
        )
        bot.send_message(msg.chat.id, text, reply_markup=buttons)


# == Free‑text shortcut (Create event wizard) ==

WIZARD_STATE = {}

@bot.message_handler(content_types=["text"], func=lambda m: m.text not in {
    "📅 My events", "🧑‍🤝‍🧑 Friends' events", "🌐 Public events", "➕ Create event", "⚙️ Settings"
})
def handle_free_text(msg: types.Message):
    user_id = msg.from_user.id
    WIZARD_STATE[user_id] = {"step": "title", "data": {"description": msg.text.strip()[:200]}}
    bot.reply_to(msg, "Great! What's the <b>title</b> of your event? (3‑80 chars)")

@bot.message_handler(func=lambda m: m.text == "➕ Create event")
def handle_create_event(msg: types.Message):
    user_id = msg.from_user.id
    WIZARD_STATE[user_id] = {"step": "title", "data": {}}
    bot.reply_to(msg, "Let's create a new event! What's the <b>title</b>? (3‑80 chars)")

# ... more wizard handlers here (title -> description -> datetime -> tags -> location -> visibility)

# == Callback Query Handler ==
@bot.callback_query_handler(func=lambda call: call.data.startswith("evt:"))
def handle_callback(call: types.CallbackQuery):
    parts = call.data.split(":")
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "ERR_BAD_ACTION")
        return
    _, event_id, _, verb = parts

    with SessionLocal() as db:
        ev = db.get(Event, event_id)
        if not ev:
            bot.answer_callback_query(call.id, "ERR_NOT_FOUND")
            return

    if verb == "details":
        send_event_details(call.message.chat.id, ev, call.from_user.id)
    elif verb == "join":
        toggle_join_event(call, ev)
    elif verb == "delete":
        delete_or_leave_event(call, ev)
    elif verb == "edit":
        start_edit_wizard(call, ev)
    elif verb == "unfriend":
        unfriend_author(call, ev)
    else:
        bot.answer_callback_query(call.id, "ERR_BAD_ACTION")

# Helper implementations -------------------------------------------------------

def user_joined_event(user_id: int, event_id: str) -> bool:
    with SessionLocal() as db:
        return db.get(Participation, {"user_id": user_id, "event_id": event_id}) is not None


def send_event_details(chat_id: int, ev: Event, viewer_id: int):
    joined_indicator = "✔️ Joined" if user_joined_event(viewer_id, ev.id) else "Join"
    text = (
        f"<b>{ev.title}</b>\n"
        f"Date: {ev.datetime_utc.strftime('%Y‑%m‑%d %H:%M UTC')}\n"
        f"Location: {ev.location_txt}\n"
        f"Tags: {ev.tags}\n\n"
        f"{ev.description}"
    )
    buttons = types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        types.InlineKeyboardButton("Deeplink", url=f"https://t.me/{bot.get_me().username}?start=evt_{ev.id}"),
        types.InlineKeyboardButton(joined_indicator, callback_data=cb(ev.id, "join"))
    )
    bot.send_message(chat_id, text, reply_markup=buttons)


def toggle_join_event(call: types.CallbackQuery, ev: Event):
    user_id = call.from_user.id
    with SessionLocal() as db:
        participation = db.get(Participation, {"user_id": user_id, "event_id": ev.id})
        if participation:
            db.delete(participation)
            db.commit()
            bot.answer_callback_query(call.id, "You left the event.")
        else:
            db.add(Participation(user_id=user_id, event_id=ev.id))
            # Friendship auto‑create
            if not db.get(Friendship, {"follower_id": user_id, "followee_id": ev.owner_id}):
                db.add(Friendship(follower_id=user_id, followee_id=ev.owner_id))
            db.commit()
            bot.answer_callback_query(call.id, "You joined the event!")


def delete_or_leave_event(call: types.CallbackQuery, ev: Event):
    user_id = call.from_user.id
    with SessionLocal() as db:
        if ev.owner_id == user_id:
            ev.state = EventState.Deleted
            db.commit()
            bot.answer_callback_query(call.id, "Event deleted.")
        else:
            part = db.get(Participation, {"user_id": user_id, "event_id": ev.id})
            if part:
                db.delete(part)
                db.commit()
                bot.answer_callback_query(call.id, "You left the event.")
            else:
                bot.answer_callback_query(call.id, "ERR_NO_PERMISSION")


def start_edit_wizard(call: types.CallbackQuery, ev: Event):
    # PoC: simplify edit by deleting & re‑creating via wizard TODO future
    bot.answer_callback_query(call.id, "Edit flow not yet implemented in PoC.")


def unfriend_author(call: types.CallbackQuery, ev: Event):
    user_id = call.from_user.id
    with SessionLocal() as db:
        fr = db.get(Friendship, {"follower_id": user_id, "followee_id": ev.owner_id})
        if fr:
            db.delete(fr)
            db.commit()
            bot.answer_callback_query(call.id, "Unfriended.")
        else:
            bot.answer_callback_query(call.id, "ERR_NOT_FOUND")

# ──────────────────────────────────────────────────────────────
# 5. Entry‑point
# ──────────────────────────────────────────────────────────────

def main():
    log.info("Starting Invevent Bot PoC…")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()

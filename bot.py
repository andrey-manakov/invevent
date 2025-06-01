# == standard library ==
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from enum import Enum as PyEnum  # Python Enum alias

# == third‑party ==
from dotenv import load_dotenv
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, create_engine,
    select, func, Text
)
from sqlalchemy import Enum as SAEnum  # SQLAlchemy Enum datatype
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


class EventVisibility(str, PyEnum):
    Public = "Public"
    Friends = "Friends"


class EventState(str, PyEnum):
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
    visibility: Mapped[EventVisibility] = mapped_column(SAEnum(EventVisibility))
    tags: Mapped[str] = mapped_column(String(120))  # CSV in PoC
    notification_offset_min: Mapped[Optional[int]] = mapped_column(Integer)
    state: Mapped[EventState] = mapped_column(SAEnum(EventState), default=EventState.Active)


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

# Create tables on first run
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

# Helper: callback payload builder / parser

def cb(event_id: str, verb: str) -> str:
    return f"evt:{event_id}:act:{verb}"

def parse_cb(data: str) -> tuple[str, str]:
    try:
        _, evt_id, _, verb = data.split(":", 3)
        return evt_id, verb
    except ValueError:
        return "", ""

# Helper: text snippet
MAX_DESC_SNIPPET = 50

def snippet(text: str, max_len: int = MAX_DESC_SNIPPET) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"

# Helper: participation check

def user_joined_event(user_id: int, event_id: str) -> bool:
    with SessionLocal() as db:
        return db.scalar(
            select(func.count()).select_from(Participation)
            .where(
                (Participation.event_id == event_id) & (Participation.user_id == user_id)
            )
        ) > 0

# ═════════════════════════════════════════════════════════════
# 4. Command & Message Handlers
# ═════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def handle_start(msg: types.Message):
    with SessionLocal() as db:
        ensure_user(db, msg.from_user)
    bot.send_message(
        msg.chat.id,
        f"<b>Hi {msg.from_user.first_name}</b>! I can help you plan and share events.\nChoose an option ↓",
        reply_markup=PERSISTENT_KB
    )

# -- util ------------------------------------------------------

def ensure_user(db, tg_user: types.User):
    u = db.get(User, tg_user.id)
    if not u:
        u = User(id=tg_user.id, first_name=tg_user.first_name, username=tg_user.username)
        db.add(u)
    else:
        if u.username != tg_user.username:
            u.username = tg_user.username
    db.commit()

# == 4.1 My events ============================================

@bot.message_handler(func=lambda m: m.text == "📅 My events")
def handle_my_events(msg: types.Message):
    user_id = msg.from_user.id
    with SessionLocal() as db:
        events = db.scalars(
            select(Event)
            .where(
                (Event.owner_id == user_id) |
                (Event.id.in_(
                    select(Participation.event_id).where(Participation.user_id == user_id)
                ))
            )
            .where(Event.state == EventState.Active)
            .order_by(Event.datetime_utc)
            .limit(10)
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
            types.InlineKeyboardButton(
                "Delete" if ev.owner_id == user_id else "Leave", callback_data=cb(ev.id, "delete")
            ),
        )
        bot.send_message(msg.chat.id, text, reply_markup=buttons)

# == 4.2 Friends' events ======================================

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
            .limit(10)
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
            types.InlineKeyboardButton(joined, callback дальнейшем📦
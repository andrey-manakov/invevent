"""Telegram bot logic."""
from datetime import datetime, timezone
import uuid
from typing import Tuple

import telebot
from telebot import types
from sqlalchemy import select, func

from .config import BOT_TOKEN
from .database import SessionLocal, Base, engine
from .models import (
    User, Event, EventState, EventVisibility,
    Participation, Friendship
)
from .wizard import WIZARDS, WIZ_STEPS, snippet, reset, start, get as wiz_get

Base.metadata.create_all(engine)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

MAIN_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
MAIN_KB.add(
    "📅 My events",
    "🧑‍🤝‍🧑 Friends' events",
    "🌐 Public events",
    "➕ Create event",
)

def ensure_user(db, tg_user: types.User):
    u = db.get(User, tg_user.id)
    if not u:
        u = User(id=tg_user.id, first_name=tg_user.first_name, username=tg_user.username)
        db.add(u)
    else:
        if u.username != tg_user.username:
            u.username = tg_user.username
    db.commit()

def cb(evt_id: str, verb: str) -> str:
    return f"evt:{evt_id}:act:{verb}"

def parse_cb(data: str) -> Tuple[str, str]:
    try:
        _, evt_id, _, verb = data.split(":", 3)
        return evt_id, verb
    except ValueError:
        return "", ""

def user_joined(db, user_id: int, event_id: str) -> bool:
    return (
        db.scalar(
            select(func.count()).select_from(Participation).where(
                (Participation.user_id == user_id) & (Participation.event_id == event_id)
            )
        )
        > 0
    )

def ensure_friendship(db, follower_id: int, followee_id: int):
    if follower_id == followee_id:
        return
    key = {"follower_id": follower_id, "followee_id": followee_id}
    if not db.get(Friendship, key):
        db.add(Friendship(**key))
        db.commit()

# ── Handlers ────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg: types.Message):
    with SessionLocal() as db:
        ensure_user(db, msg.from_user)
    bot.send_message(
        msg.chat.id,
        f"<b>Hi {msg.from_user.first_name}!</b>\nPlan, share & join outings.",
        reply_markup=MAIN_KB,
    )

@bot.message_handler(func=lambda m: m.text == "➕ Create event")
def create_event(msg: types.Message):
    start(msg.from_user.id)
    bot.reply_to(msg, "Event title?")

@bot.message_handler(func=lambda m: True)  # Wizard flow / ignore others
def wizard_flow(msg: types.Message):
    uid = msg.from_user.id
    wiz = wiz_get(uid)
    if not wiz:
        return
    step = WIZ_STEPS[wiz["step"]]
    if step == "title":
        wiz["title"] = snippet(msg.text, 80)
        wiz["step"] += 1
        bot.reply_to(msg, "Description?")
    elif step == "description":
        wiz["description"] = snippet(msg.text, 160)
        wiz["step"] += 1
        bot.reply_to(msg, "Date & time (YYYY‑MM‑DD HH:MM)?")
    elif step == "datetime":
        try:
            local_dt = datetime.strptime(msg.text.strip(), "%Y-%m-%d %H:%M")
            wiz["datetime_utc"] = local_dt.replace(tzinfo=timezone.utc)
            wiz["step"] += 1
            bot.reply_to(msg, "Location?")
        except ValueError:
            bot.reply_to(msg, "❌ Wrong format.")
    elif step == "location":
        wiz["location_txt"] = snippet(msg.text, 120)
        wiz["step"] += 1
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add("Public", "Friends")
        bot.reply_to(msg, "Visibility?", reply_markup=kb)
    elif step == "visibility":
        choice = msg.text.capitalize()
        if choice not in ["Public", "Friends"]:
            bot.reply_to(msg, "Choose Public or Friends")
            return
        wiz["visibility"] = EventVisibility(choice)
        wiz["step"] += 1
        summary = (
            f"<b>{wiz['title']}</b>\n{wiz['description']}\n\n"
            f"🗓️ {wiz['datetime_utc'].strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📍 {wiz['location_txt']}\n"
            f"🔒 {wiz['visibility'].value}"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Create", callback_data="wizard:create"),
               types.InlineKeyboardButton("Cancel", callback_data="wizard:cancel"))
        bot.reply_to(msg, summary, reply_markup=kb)

@bot.callback_query_handler(func=lambda cq: cq.data.startswith("wizard:"))
def wizard_cb(cq: types.CallbackQuery):
    action = cq.data.split(":")[1]
    uid = cq.from_user.id
    wiz = wiz_get(uid)
    if not wiz:
        bot.answer_callback_query(cq.id, "Wizard expired.", show_alert=True)
        return
    if action == "cancel":
        reset(uid)
        bot.answer_callback_query(cq.id, "Cancelled")
        return
    if action == "create":
        with SessionLocal() as db:
            ev = Event(
                id=str(uuid.uuid4()),
                owner_id=uid,
                title=wiz["title"],
                description=wiz["description"],
                datetime_utc=wiz["datetime_utc"],
                location_txt=wiz["location_txt"],
                visibility=wiz["visibility"],
                tags="",
            )
            db.add(ev)
            db.commit()
        reset(uid)
        bot.answer_callback_query(cq.id, "Event created!")

# --- expose bot ---
def run():
    bot.infinity_polling()

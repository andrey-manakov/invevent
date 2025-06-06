from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from ..database import SessionLocal
from ..models import Event, Participation, EventState, EventVisibility, Friendship
from ..helpers import cb
from .state import set_state


def register(bot):
    @bot.message_handler(regexp=r"^/start")
    def handle_start_cmd(msg):
        parts = msg.text.split(maxsplit=1)
        user_id = msg.from_user.id

        if len(parts) < 2:
            from ..bot import MAIN_KB
            bot.send_message(
                user_id,
                f"<b>Hi {msg.from_user.first_name}!</b>\nPlan, share & join outings!!!",
                parse_mode="HTML",
                reply_markup=MAIN_KB
            )
            set_state(user_id, "main")
            return

        param = parts[1]

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


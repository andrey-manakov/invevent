from datetime import datetime, timezone
from telebot import types
from telebot.handler_backends import ContinueHandling
from sqlalchemy import select, func

from ..database import SessionLocal
from ..models import User, Event, Friendship, EventState
from ..helpers import ucb
from .state import set_state, get_state
from .events_menu import _list_events, LIST_KB

# Keyboards
FRIENDS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
FRIENDS_KB.add("🙋 Followers", "👍 Followed", "⬅️ Back")

BACK_KB = types.ReplyKeyboardMarkup(resize_keyboard=True)
BACK_KB.add("⬅️ Back")

USER_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
USER_KB.add("🚫 Unfollow", "🗑 Unfriend", "📅 Events", "⬅️ Back", "🏠 Main menu")

# Context information about selected friend
USER_CTX = {}


def register(bot):
    def show_followers(chat_id: int, uid: int) -> None:
        set_state(uid, "followers")
        with SessionLocal() as db:
            ids = db.scalars(select(Friendship.follower_id).where(Friendship.followee_id == uid)).all()
            users = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            kb = types.InlineKeyboardMarkup()
            for u in users:
                cnt = db.scalar(
                    select(func.count()).select_from(Event).where(
                        Event.owner_id == u.id,
                        Event.state == EventState.Active,
                        Event.datetime_utc >= today,
                    )
                )
                kb.add(types.InlineKeyboardButton(f"{u.first_name} ({cnt})", callback_data=ucb(u.id, "menu")))
        text = "<b>Followers:</b>"
        if not users:
            text += "\n(none)"
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
        bot.send_message(chat_id, "Options:", reply_markup=BACK_KB)

    def show_followed(chat_id: int, uid: int) -> None:
        set_state(uid, "followed")
        with SessionLocal() as db:
            ids = db.scalars(select(Friendship.followee_id).where(Friendship.follower_id == uid)).all()
            users = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            kb = types.InlineKeyboardMarkup()
            for u in users:
                cnt = db.scalar(
                    select(func.count()).select_from(Event).where(
                        Event.owner_id == u.id,
                        Event.state == EventState.Active,
                        Event.datetime_utc >= today,
                    )
                )
                kb.add(types.InlineKeyboardButton(f"{u.first_name} ({cnt})", callback_data=ucb(u.id, "menu")))
        text = "<b>Followed:</b>"
        if not users:
            text += "\n(none)"
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
        bot.send_message(chat_id, "Options:", reply_markup=BACK_KB)

    def show_user_menu(chat_id: int, uid: int, friend_id: int, origin: str) -> None:
        with SessionLocal() as db:
            user = db.get(User, friend_id)
        name = user.first_name if user else str(friend_id)
        USER_CTX[uid] = {"id": friend_id, "name": name, "origin": origin}
        set_state(uid, "friend_user")
        bot.send_message(chat_id, f"<b>{name}</b>", parse_mode="HTML", reply_markup=USER_KB)

    def show_friend_events(chat_id: int, uid: int) -> None:
        ctx = USER_CTX.get(uid)
        if not ctx:
            return
        fid = ctx["id"]
        name = ctx["name"]
        set_state(uid, "friend_events")
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.owner_id == fid,
                    Event.state == EventState.Active,
                    Event.datetime_utc >= today,
                )
            ).all()
        text, ikb = _list_events(uid, events)
        header = f"<b>{name}'s events:</b>"
        if text:
            header += "\n" + text
        bot.send_message(chat_id, header, parse_mode="HTML", reply_markup=ikb)
        bot.send_message(chat_id, "Options:", reply_markup=LIST_KB)

    @bot.message_handler(func=lambda m: m.text == "👥 Friends")
    def friends_main(msg):
        uid = msg.from_user.id
        set_state(uid, "friends")
        bot.send_message(msg.chat.id, "Friends:", reply_markup=FRIENDS_KB)

    @bot.message_handler(func=lambda m: m.text == "🙋 Followers")
    def followers(msg):
        show_followers(msg.chat.id, msg.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "👍 Followed")
    def followed(msg):
        show_followed(msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("user:"))
    def user_callback(c):
        _, uid_str, _, act = c.data.split(":")
        fid = int(uid_str)
        if act == "menu":
            origin = get_state(c.from_user.id)
            show_user_menu(c.message.chat.id, c.from_user.id, fid, origin)
        bot.answer_callback_query(c.id)

    @bot.message_handler(func=lambda m: m.text == "🚫 Unfollow")
    def unfollow(msg):
        if get_state(msg.from_user.id) != "friend_user":
            return
        ctx = USER_CTX.get(msg.from_user.id)
        if not ctx:
            return
        fid = ctx["id"]
        with SessionLocal() as db:
            rel = db.get(Friendship, {"follower_id": msg.from_user.id, "followee_id": fid})
            if rel:
                db.delete(rel)
                db.commit()
        bot.reply_to(msg, "You have unfollowed this user.")

    @bot.message_handler(func=lambda m: m.text == "🗑 Unfriend")
    def unfriend(msg):
        if get_state(msg.from_user.id) != "friend_user":
            return
        ctx = USER_CTX.get(msg.from_user.id)
        if not ctx:
            return
        fid = ctx["id"]
        with SessionLocal() as db:
            rel1 = db.get(Friendship, {"follower_id": msg.from_user.id, "followee_id": fid})
            rel2 = db.get(Friendship, {"follower_id": fid, "followee_id": msg.from_user.id})
            if rel1:
                db.delete(rel1)
            if rel2:
                db.delete(rel2)
            db.commit()
        bot.reply_to(msg, "Friendship removed.")

    @bot.message_handler(func=lambda m: m.text == "📅 Events")
    def user_events(msg):
        if get_state(msg.from_user.id) != "friend_user":
            return
        show_friend_events(msg.chat.id, msg.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "📍 Show on map")
    def show_on_map(msg):
        if get_state(msg.from_user.id) != "friend_events":
            return
        ctx = USER_CTX.get(msg.from_user.id)
        if not ctx:
            return
        fid = ctx["id"]
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.owner_id == fid,
                    Event.state == EventState.Active,
                    Event.datetime_utc >= today,
                )
            ).all()
        from ..map_view import show_events_on_map
        show_events_on_map(bot, msg.chat.id, events)

    @bot.message_handler(func=lambda m: m.text == "📍 Nearby")
    def nearby_request(msg):
        if get_state(msg.from_user.id) != "friend_events":
            return
        set_state(msg.from_user.id, "friend_nearby_wait")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
        kb.add("⬅️ Back")
        bot.send_message(msg.chat.id, "Send your location to see nearby events:", reply_markup=kb)

    @bot.message_handler(content_types=["location"])
    def nearby_location(msg):
        if get_state(msg.from_user.id) != "friend_nearby_wait":
            return ContinueHandling()
        set_state(msg.from_user.id, "friend_events")
        ctx = USER_CTX.get(msg.from_user.id)
        if not ctx:
            return
        fid = ctx["id"]
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        with SessionLocal() as db:
            events = db.scalars(
                select(Event).where(
                    Event.owner_id == fid,
                    Event.state == EventState.Active,
                    Event.datetime_utc >= today,
                )
            ).all()
        from ..map_view import show_events_on_map, filter_nearby_events
        nearby = filter_nearby_events(events, msg.location.latitude, msg.location.longitude)
        show_events_on_map(bot, msg.chat.id, nearby)

    @bot.message_handler(func=lambda m: m.text == "🏠 Main menu")
    def to_main(msg):
        if get_state(msg.from_user.id) not in ("friend_user", "friend_events", "friend_nearby_wait"):
            return
        from ..bot import MAIN_KB
        set_state(msg.from_user.id, "main")
        bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Back")
    def back(msg):
        uid = msg.from_user.id
        state = get_state(uid)
        if state == "friend_nearby_wait":
            set_state(uid, "friend_events")
            bot.send_message(msg.chat.id, "Options:", reply_markup=LIST_KB)
        elif state == "friend_events":
            set_state(uid, "friend_user")
            bot.send_message(msg.chat.id, "Select:", reply_markup=USER_KB)
        elif state == "friend_user":
            ctx = USER_CTX.get(uid)
            origin = ctx.get("origin") if ctx else "friends"
            if origin == "followers":
                show_followers(msg.chat.id, uid)
            elif origin == "followed":
                show_followed(msg.chat.id, uid)
            else:
                set_state(uid, "friends")
                bot.send_message(msg.chat.id, "Friends:", reply_markup=FRIENDS_KB)
        elif state in ("followers", "followed"):
            set_state(uid, "friends")
            bot.send_message(msg.chat.id, "Friends:", reply_markup=FRIENDS_KB)
        elif state == "friends":
            from ..bot import MAIN_KB
            set_state(uid, "main")
            bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)

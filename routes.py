import uuid
from datetime import datetime, timezone
from telebot import types
from sqlalchemy import select
from .database import SessionLocal, Base, engine
from .models import User, Event, Participation, Friendship, EventState, EventVisibility
from .wizard import start as wiz_start, reset as wiz_reset, get as wiz_get, STEPS, snippet

Base.metadata.create_all(engine)

TAGS=["🎉 Party","🎮 Gaming","🍽️ Food","🎬 Cinema"]

def ensure_user(db,tg_user):
    u=db.get(User,tg_user.id)
    if not u:
        u=User(id=tg_user.id,first_name=tg_user.first_name,username=tg_user.username)
        db.add(u)
    elif tg_user.username and u.username!=tg_user.username:
        u.username=tg_user.username
    db.commit()

def main_kb():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    kb.add("📅 My events","🧑‍🤝‍🧑 Friends' events","🌐 Public events","➕ Create event")
    return kb

def cb(eid:str,verb:str)->str:
    return f"evt:{eid}:act:{verb}"

def register_routes(bot):

    # /start
    @bot.message_handler(commands=["start"])
    def _start(m):
        with SessionLocal() as db:
            ensure_user(db,m.from_user)
        bot.send_message(m.chat.id,f"<b>Hi {m.from_user.first_name}!</b>\nPlan, share & join outings. in routes",
                         parse_mode="HTML",reply_markup=main_kb())

    # My events
    @bot.message_handler(func=lambda m: m.text=="📅 My events")
    def my_events(m):
        uid=m.from_user.id
        with SessionLocal() as db:
            events_owned=db.scalars(select(Event).where(Event.owner_id==uid, Event.state==EventState.Active)).all()
            events_joined=db.scalars(select(Event).join(Participation, Participation.event_id==Event.id)
                                     .where(Participation.user_id==uid, Event.state==EventState.Active)).all()
        seen={e.id for e in events_owned}
        events=events_owned + [e for e in events_joined if e.id not in seen]
        if not events:
            bot.reply_to(m,"No upcoming events.");return
        for ev in events:
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Details",callback_data=cb(ev.id,"details")))
            if ev.owner_id==uid:
                kb.add(types.InlineKeyboardButton("Delete",callback_data=cb(ev.id,"delete")))
            else:
                kb.add(types.InlineKeyboardButton("Unjoin",callback_data=cb(ev.id,"unjoin")))
            bot.send_message(m.chat.id,f"<b>{ev.title}</b> — {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n{snippet(ev.description,120)}",
                             parse_mode="HTML",reply_markup=kb)

    # (other handlers trimmed for brevity)

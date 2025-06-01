import uuid
from datetime import datetime, timezone
from telebot import types
from sqlalchemy import select, func

from .models import (User, Event, EventState, EventVisibility,
                     Participation, Friendship)
from .database import SessionLocal, Base, engine
from .wizard import start as wiz_start, reset as wiz_reset, get as wiz_get, STEPS as WIZ_STEPS, snippet

# Ensure tables
Base.metadata.create_all(engine)

TAGS = ["🎉 Party","🎮 Gaming","🍽️ Food","🎬 Cinema","🏞️ Outdoor","🎵 Concert"]

def ensure_user(db, tg_user):
    u = db.get(User, tg_user.id)
    if not u:
        u = User(id=tg_user.id, first_name=tg_user.first_name, username=tg_user.username)
        db.add(u)
    elif tg_user.username and u.username != tg_user.username:
        u.username = tg_user.username
    db.commit()

def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    kb.add("📅 My events","🧑‍🤝‍🧑 Friends' events",
           "🌐 Public events","➕ Create event")
    return kb

def cb(evt_id:str,verb:str)->str:
    return f"evt:{evt_id}:act:{verb}"

def parse_cb(data:str):
    try:
        _,eid,_,verb=data.split(":",3)
        return eid,verb
    except ValueError:
        return "",""

def register_routes(bot):

    # /start
    @bot.message_handler(commands=["start"])
    def cmd_start(msg):
        with SessionLocal() as db:
            ensure_user(db,msg.from_user)
        bot.send_message(msg.chat.id,
                         f"<b>Hi {msg.from_user.first_name}!</b>\nPlan, share & join outings.",
                         parse_mode="HTML",
                         reply_markup=main_kb())

    # Main menu buttons
    @bot.message_handler(func=lambda m: m.text=="📅 My events")
    def my_events(msg):
        uid=msg.from_user.id
        with SessionLocal() as db:
            q_owned=select(Event).where(Event.owner_id==uid,Event.state==EventState.Active)
            q_join=select(Event).join(Participation,Participation.event_id==Event.id)                         .where(Participation.user_id==uid,Event.state==EventState.Active)
            events=db.scalars(q_owned.union(q_join).order_by(Event.datetime_utc)).all()
        if not events:
            bot.reply_to(msg,"No upcoming events.")
            return
        for ev in events:
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Details",callback_data=cb(ev.id,"details")))
            if ev.owner_id==uid:
                kb.add(types.InlineKeyboardButton("Edit",callback_data=cb(ev.id,"edit")),
                       types.InlineKeyboardButton("Delete",callback_data=cb(ev.id,"delete")))
            else:
                kb.add(types.InlineKeyboardButton("Unjoin",callback_data=cb(ev.id,"unjoin")))
            bot.send_message(msg.chat.id,
                             f"<b>{ev.title}</b> — {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n{snippet(ev.description,120)}",
                             parse_mode="HTML",reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text=="🧑‍🤝‍🧑 Friends' events")
    def friends_events(msg):
        uid=msg.from_user.id
        with SessionLocal() as db:
            friend_ids=db.scalars(select(Friendship.followee_id).where(Friendship.follower_id==uid)).all()
            events=db.scalars(select(Event).where(Event.owner_id.in_(friend_ids),
                                                  Event.state==EventState.Active)).all()
        if not events:
            bot.reply_to(msg,"No events from friends.")
            return
        for ev in events:
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Details",callback_data=cb(ev.id,"details")),
                   types.InlineKeyboardButton("Join",callback_data=cb(ev.id,"join")),
                   types.InlineKeyboardButton("Unfollow",callback_data=f"unfollow:{ev.owner_id}"))
            bot.send_message(msg.chat.id,f"<b>{ev.title}</b> — {ev.datetime_utc:%Y-%m-%d %H:%M UTC}",parse_mode="HTML",reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text=="🌐 Public events")
    def public_events(msg):
        uid=msg.from_user.id
        with SessionLocal() as db:
            evs=db.scalars(select(Event).where(Event.visibility==EventVisibility.Public,
                                               Event.state==EventState.Active)).all()
        if not evs:
            bot.reply_to(msg,"No public events.")
            return
        for ev in evs:
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Details",callback_data=cb(ev.id,"details")),
                   types.InlineKeyboardButton("Join",callback_data=cb(ev.id,"join")))
            bot.send_message(msg.chat.id,f"<b>{ev.title}</b> — {ev.datetime_utc:%Y-%m-%d %H:%M}",parse_mode="HTML",reply_markup=kb)

    # Create event button
    @bot.message_handler(func=lambda m: m.text=="➕ Create event")
    def create_event(msg):
        wiz_start(msg.from_user.id)
        bot.reply_to(msg,"Event title?")

    # Wizard or free text
    @bot.message_handler(func=lambda m: True)
    def wizard_or_quick(msg):
        uid=msg.from_user.id
        wiz=wiz_get(uid)
        if not wiz:
            # treat as quick create start using description
            wiz_start(uid)
            wiz=wiz_get(uid)
            wiz["description"]=snippet(msg.text)
            wiz["step"]=2  # expecting datetime
            bot.reply_to(msg,"Event title?")
            return

        step=WIZ_STEPS[wiz["step"]]
        if step=="title":
            wiz["title"]=snippet(msg.text,80)
            wiz["step"]+=1
            bot.reply_to(msg,"Description?")
        elif step=="description":
            wiz["description"]=snippet(msg.text,200)
            wiz["step"]+=1
            bot.reply_to(msg,"Date & time YYYY-MM-DD HH:MM?")
        elif step=="datetime":
            try:
                dt=datetime.strptime(msg.text,"%Y-%m-%d %H:%M")
                wiz["datetime_utc"]=dt.replace(tzinfo=timezone.utc)
                wiz["step"]+=1
                kb=types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True,row_width=3)
                kb.add(*TAGS, "done")
                bot.reply_to(msg,"Add tags (one per message) or 'done'.",reply_markup=kb)
            except ValueError:
                bot.reply_to(msg,"Wrong format, try again.")
        elif step=="tags":
            if msg.text.lower()=="done":
                wiz["step"]+=1
                bot.reply_to(msg,"Location text?")
            else:
                wiz.setdefault("tags",[]).append(snippet(msg.text,20))
        elif step=="location":
            wiz["location_txt"]=snippet(msg.text,120)
            wiz["step"]+=1
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True)
            kb.add("Public","Friends")
            bot.reply_to(msg,"Visibility?",reply_markup=kb)
        elif step=="visibility":
            choice=msg.text.capitalize()
            if choice not in ["Public","Friends"]:
                bot.reply_to(msg,"Choose Public or Friends")
                return
            wiz["visibility"]=EventVisibility(choice)
            # Confirm
            summary=(f"<b>{wiz['title']}</b>\n{wiz['description']}\n\n"
                     f"{wiz['datetime_utc']:%Y-%m-%d %H:%M UTC}\n📍{wiz['location_txt']}\n"
                     f"🏷️ {', '.join(wiz.get('tags',[]))}\n🔒{wiz['visibility'].value}")
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Create",callback_data="wizard:create"),
                   types.InlineKeyboardButton("Cancel",callback_data="wizard:cancel"))
            bot.reply_to(msg,summary,parse_mode="HTML",reply_markup=kb)

    # Wizard callbacks
    @bot.callback_query_handler(func=lambda c: c.data.startswith("wizard:"))
    def wizard_cb(c):
        uid=c.from_user.id
        wiz=wiz_get(uid)
        if not wiz:
            bot.answer_callback_query(c.id,"Wizard expired",show_alert=True); return
        action=c.data.split(":")[1]
        if action=="cancel":
            wiz_reset(uid); bot.answer_callback_query(c.id,"Cancelled"); return
        if action=="create":
            with SessionLocal() as db:
                ev=Event(id=str(uuid.uuid4()),
                         owner_id=uid,
                         title=wiz["title"],
                         description=wiz["description"],
                         datetime_utc=wiz["datetime_utc"],
                         location_txt=wiz["location_txt"],
                         visibility=wiz["visibility"],
                         tags=",".join(wiz.get("tags",[])))
                db.add(ev); db.commit()
            wiz_reset(uid); bot.answer_callback_query(c.id,"Created!")

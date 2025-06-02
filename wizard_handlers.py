"""Full create‑event wizard handlers"""
import uuid
from datetime import datetime, timezone
from telebot import types
from .wizard import STEPS, start as wiz_start, get as wiz_get, reset as wiz_reset, snippet
from .models import Event, EventVisibility
from .database import SessionLocal
TAGS = ["🎉 Party","🎮 Gaming","🍽️ Food","🎬 Cinema"]

def register_wizard(bot):

    @bot.message_handler(func=lambda m: m.text == "➕ Create event")
    def start(m):
        wiz_start(m.from_user.id)
        bot.reply_to(m,"Event title?")

    @bot.message_handler(func=lambda m: True)
    def flow(m):
        w = wiz_get(m.from_user.id)
        if not w: return
        step = STEPS[w["step"]]
        if step == "title":
            w["title"] = snippet(m.text,80); w["step"] += 1
            bot.reply_to(m,"Description?")
        elif step == "description":
            w["description"] = snippet(m.text,200); w["step"] += 1
            bot.reply_to(m,"Date & time YYYY-MM-DD HH:MM?")
        elif step == "datetime":
            try:
                dt = datetime.strptime(m.text,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                w["datetime_utc"] = dt; w["step"] += 1
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True,row_width=3)
                kb.add(*TAGS,"done")
                bot.reply_to(m,"Tag (repeat) then 'done':",reply_markup=kb)
            except ValueError:
                bot.reply_to(m,"Wrong format.")
        elif step == "tags":
            if m.text.lower()=="done":
                w["step"] += 1; bot.reply_to(m,"Location?")
            else:
                w.setdefault("tags",[]).append(snippet(m.text,20))
        elif step == "location":
            w["location_txt"] = snippet(m.text,120); w["step"] += 1
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True)
            kb.add("Public","Friends")
            bot.reply_to(m,"Visibility?",reply_markup=kb)
        elif step == "visibility":
            vis = m.text.capitalize()
            if vis not in ["Public","Friends"]:
                bot.reply_to(m,"Choose Public or Friends"); return
            w["visibility"] = EventVisibility(vis); w["step"] += 1
            summary=(f"<b>{w['title']}</b>\n{w['description']}\n\n🗓️ {w['datetime_utc']:%Y-%m-%d %H:%M UTC}"
                     f"\n📍{w['location_txt']}\n🏷️ {', '.join(w.get('tags',[]))}\n🔒{w['visibility'].value}")
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Create",callback_data="wiz:create"),
                   types.InlineKeyboardButton("Cancel",callback_data="wiz:cancel"))
            bot.reply_to(m,summary,parse_mode="HTML",reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data in ("wiz:create","wiz:cancel"))
    def done(c):
        w=wiz_get(c.from_user.id)
        if not w:
            bot.answer_callback_query(c.id,"Expired"); return
        if c.data=="wiz:cancel":
            wiz_reset(c.from_user.id); bot.answer_callback_query(c.id,"Cancelled"); return
        with SessionLocal() as db:
            ev=Event(id=str(uuid.uuid4()), owner_id=c.from_user.id,
                     title=w["title"], description=w["description"],
                     datetime_utc=w["datetime_utc"], location_txt=w["location_txt"],
                     visibility=w["visibility"], tags=",".join(w.get("tags",[])))
            db.add(ev); db.commit()
        wiz_reset(c.from_user.id)
        bot.answer_callback_query(c.id,"Created!")

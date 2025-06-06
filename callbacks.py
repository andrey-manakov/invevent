
from telebot import types
from sqlalchemy import select
from .database import SessionLocal
from .models import Event, Participation, EventState
from .helpers import cb

def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda c: c.data.startswith("evt:"))
    def evt_cb(c):
        _, eid, _, verb = c.data.split(":")
        with SessionLocal() as db:
            ev = db.get(Event, eid)
            if not ev:
                bot.answer_callback_query(c.id,"Not found"); return
            if verb=="details":
                text=(f"<b>{ev.title}</b>\n{ev.description}\n\n🗓️ {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n📍{ev.location_txt}")
                bot.answer_callback_query(c.id); bot.send_message(c.message.chat.id,text,parse_mode="HTML")
            elif verb=="join":
                db.add(Participation(event_id=eid,user_id=c.from_user.id)); db.commit()
                bot.answer_callback_query(c.id,"Joined!")
            elif verb=="unjoin":
                part=db.get(Participation,{"event_id":eid,"user_id":c.from_user.id})
                if part: db.delete(part); db.commit()
                bot.answer_callback_query(c.id,"Unjoined!")
            elif verb=="delete" and ev.owner_id==c.from_user.id:
                ev.state=EventState.Deleted; db.commit()
                bot.answer_callback_query(c.id,"Deleted")
            elif verb=="summary":
                part=db.get(Participation,{"event_id":eid,"user_id":c.from_user.id})
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("Details",callback_data=cb(eid,"details")))
                if c.from_user.id==ev.owner_id:
                    kb.add(types.InlineKeyboardButton("Delete",callback_data=cb(eid,"delete")))
                else:
                    if part:
                        kb.add(types.InlineKeyboardButton("Unjoin",callback_data=cb(eid,"unjoin")))
                    else:
                        kb.add(types.InlineKeyboardButton("Join",callback_data=cb(eid,"join")))
                text=(f"<b>{ev.title}</b>\n"
                      f"🗓️ {ev.datetime_utc:%Y-%m-%d %H:%M UTC}\n"
                      f"📍{ev.location_txt}")
                bot.answer_callback_query(c.id)
                bot.send_message(c.message.chat.id,text,parse_mode="HTML",reply_markup=kb)

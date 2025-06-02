from telebot import TeleBot, types
import os, logging
from datetime import datetime, timezone
from dotenv import load_dotenv

"""Single‑file PoC bot inside a package (invevent.bot).
Stores events in memory so you can test easily.
"""

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

EVENTS = []
WIZARDS = {}
STEPS = ["title", "description", "datetime", "confirm"]

MAIN_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
MAIN_KB.add("📅 My events", "🧑‍🤝‍🧑 Friends' events",
            "🌐 Public events", "➕ Create event")

def start_wizard(uid):
    WIZARDS[uid] = {"step": 0}

def wizard(uid):
    return WIZARDS.get(uid)

def reset_wizard(uid):
    WIZARDS.pop(uid, None)

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(msg.chat.id,
                     f"<b>Hi {msg.from_user.first_name}!</b>\nPlan, share & join outings.",
                     parse_mode="HTML", reply_markup=MAIN_KB)

@bot.message_handler(func=lambda m: m.text == "➕ Create event")
def create_event(msg):
    start_wizard(msg.from_user.id)
    bot.reply_to(msg, "Event title?")

@bot.message_handler(func=lambda m: True)
def wizard_flow(msg):
    uid = msg.from_user.id
    w = wizard(uid)
    if not w:
        return
    step = STEPS[w["step"]]
    if step == "title":
        w["title"] = msg.text[:80]
        w["step"] += 1
        bot.reply_to(msg, "Description?")
    elif step == "description":
        w["description"] = msg.text[:200]
        w["step"] += 1
        bot.reply_to(msg, "Date & time YYYY-MM-DD HH:MM?")
    elif step == "datetime":
        try:
            dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            w["datetime"] = dt
            w["step"] += 1
            summary = (f"<b>{w['title']}</b>\n{w['description']}\n\n🗓️ {dt:%Y-%m-%d %H:%M UTC}")
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Create", callback_data="wiz:create"),
                   types.InlineKeyboardButton("Cancel", callback_data="wiz:cancel"))
            bot.reply_to(msg, summary, parse_mode="HTML", reply_markup=kb)
        except ValueError:
            bot.reply_to(msg, "Wrong format. Try YYYY-MM-DD HH:MM")

@bot.callback_query_handler(func=lambda c: c.data.startswith("wiz:"))
def wizard_cb(c):
    uid = c.from_user.id
    w = wizard(uid)
    if not w:
        bot.answer_callback_query(c.id, "Wizard expired", show_alert=True)
        return
    if c.data == "wiz:cancel":
        reset_wizard(uid)
        bot.answer_callback_query(c.id, "Cancelled")
    elif c.data == "wiz:create":
        EVENTS.append(dict(id=len(EVENTS)+1, owner=uid,
                           title=w["title"], description=w["description"],
                           datetime=w["datetime"]))
        reset_wizard(uid)
        bot.answer_callback_query(c.id, "Event created!")

@bot.message_handler(func=lambda m: m.text == "📅 My events")
def my_events(msg):
    evs = [e for e in EVENTS if e["owner"] == msg.from_user.id]
    if not evs:
        bot.reply_to(msg, "No events yet. Use ➕ Create event")
        return
    for e in evs:
        bot.send_message(msg.chat.id,
                         f"<b>{e['title']}</b> — {e['datetime']:%Y-%m-%d %H:%M UTC}\n{e['description']}",
                         parse_mode="HTML")

def main():
    log.info("Bot polling ...")
    bot.infinity_polling(skip_pending=True, timeout=30)

if __name__ == "__main__":
    main()
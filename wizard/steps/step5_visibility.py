# wizard/steps/step5_visibility.py

import uuid
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from invevent.models   import Event, EventVisibility
from invevent.database import SessionLocal
from invevent.wizard   import reset as wiz_reset
# from invevent.bot      import MAIN_KB

def handle(bot, m, w):
    """
    step 5: user tapped “public” or “private” or “back.”
    Once visibility is chosen, create the Event record and send the summary.
    """
    user_id = m.from_user.id

    # 1) Back → go to step 4
    if m.text == "back":
        w["step"] = 4
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("moscow", "back", "cancel")
        bot.send_message(user_id, "Location? (tap “moscow”)", reply_markup=kb)
        return

    # 2) Must be “public” or “private”
    if m.text not in ("public", "private"):
        bot.send_message(
            user_id,
            "Please tap “public”, “private”, “back”, or “cancel”."
        )
        return

    # 3) Store visibility enum
    w["visibility"] = (
        EventVisibility.Public
        if m.text == "public"
        else EventVisibility.Private
    )

    # 4) Create the Event in the database
    with SessionLocal() as db:
        ev = Event(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            title=w["title"],
            description=w["description"],
            datetime_utc=w["datetime_utc"],
            location_txt=w["location_txt"],
            visibility=w["visibility"],
            tags=",".join(w.get("tags", []))
        )
        db.add(ev)
        db.commit()

    # 5) Build deep‐links (description & join)
    desc_link = f"https://t.me/InvEventBot?start={ev.id}&show=description"
    join_link = f"https://t.me/InvEventBot?start={ev.id}&action=join"

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("description", url=desc_link),
        InlineKeyboardButton("join", url=join_link)
    )

    # 6) Send summary (no description text) with inline buttons
    summary = (
        f"<b>{w['title']}</b>\n"
        f"🗓️ {w['datetime_utc']:%Y-%m-%d %H:%M UTC}\n"
        f"📍 {w['location_txt']}\n"
        f"🔒 {'Private' if w['visibility'] == EventVisibility.Private else 'Public'}"
    )
    bot.send_message(user_id, summary, parse_mode="HTML", reply_markup=inline_kb)

    # 7) Reset wizard, go back to main menu
    wiz_reset(user_id)
    # Defer MAIN_KB import to here, not at module top
    from invevent.bot import MAIN_KB
    bot.send_message(user_id, "Event created! Back to main menu.", reply_markup=MAIN_KB)
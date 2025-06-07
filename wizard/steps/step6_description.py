# wizard/steps/step6_description.py

import uuid
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from invevent.models import Event, EventVisibility
from invevent.database import SessionLocal
from invevent.wizard import reset as wiz_reset
from invevent.map_view import _geocode_address


def handle(bot, m, w):
    """Final step: optional description and event creation."""
    user_id = m.from_user.id

    if m.text == "back":
        w["step"] = 5
        from .step5_picture import handle as step5_handle
        step5_handle(bot, m, w)
        return

    if m.text == "skip":
        w["description"] = ""
    elif m.text is not None:
        w["description"] = m.text
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        kb.add("skip", "back", "cancel")
        bot.send_message(user_id, "Add a description or tap skip:", reply_markup=kb)
        return

    # Build location text and geocode if needed
    if w.get("address"):
        w["location_txt"] = w["address"]
    elif w.get("latitude") is not None and w.get("longitude") is not None:
        w["location_txt"] = f"{w['latitude']},{w['longitude']}"
    else:
        w["location_txt"] = ""

    if w.get("address") and (w.get("latitude") is None or w.get("longitude") is None):
        coords = _geocode_address(w["address"])
        if coords:
            w["latitude"], w["longitude"] = coords

    # Create event
    with SessionLocal() as db:
        ev = Event(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            title=w["title"],
            description=w.get("description", ""),
            datetime_utc=w["datetime_utc"],
            location_txt=w.get("location_txt", ""),
            latitude=w.get("latitude"),
            longitude=w.get("longitude"),
            address=w.get("address"),
            visibility=w["visibility"],
            tags=w.get("topic", ""),
        )
        db.add(ev)
        db.commit()

    desc_link = f"https://t.me/InvEventBot?start=desc_{ev.id}"
    join_link = f"https://t.me/InvEventBot?start=join_{ev.id}"
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("description", url=desc_link),
        InlineKeyboardButton("join", url=join_link),
    )

    loc_txt = w.get("location_txt", "")
    if "," in loc_txt:
        lat, lon = loc_txt.split(",", 1)
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        location_display = f'<a href="{map_url}">Посмотреть на карте</a>'
    else:
        location_display = loc_txt

    summary = (
        f"<b>{w['title']}</b>\n"
        f"🗓️ {w['datetime_utc']:%Y-%m-%d %H:%M UTC}\n"
        f"📍 {location_display}\n"
        f"🔒 {'Private' if w['visibility'] == EventVisibility.Private else 'Public'}"
    )

    if w.get("photo_file_id"):
        bot.send_photo(user_id, w["photo_file_id"], caption=summary, parse_mode="HTML", reply_markup=inline_kb)
    else:
        bot.send_message(user_id, summary, parse_mode="HTML", reply_markup=inline_kb)

    wiz_reset(user_id)
    from invevent.bot import MAIN_KB
    bot.send_message(user_id, "Event created! Back to main menu.", reply_markup=MAIN_KB)

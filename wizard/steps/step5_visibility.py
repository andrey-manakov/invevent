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

    # 1) Back → return to step 4 (location)
    if m.text == "back":
        w["step"] = 4
        from .step4_location import handle as step4_handle
        # Re‐invoke step4 handler to re‐send the map/text location keyboard
        step4_handle(bot, m, w)
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
    #    Build `location_txt` was already set in step 5; include latitude/longitude/address as well.

    if w.get("address"):
        w["location_txt"] = w["address"]
    elif w.get("latitude") is not None and w.get("longitude") is not None:
        w["location_txt"] = f"{w['latitude']},{w['longitude']}"
    else:
        w["location_txt"] = ""

    with SessionLocal() as db:
        ev = Event(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            title=w["title"],
            description=w["description"],
            datetime_utc=w["datetime_utc"],
            location_txt=w.get("location_txt", ""),
            latitude=w.get("latitude", None),
            longitude=w.get("longitude", None),
            address=w.get("address", None),
            visibility=w["visibility"],
            # Only one tag is supported. It was saved under ``tag`` in step 3.
            tags=w.get("tag", "")
        )        
        db.add(ev)
        db.commit()

    # 5) Build deep‐links (description & join)
    desc_link = f"https://t.me/InvEventBot?start=desc_{ev.id}"
    join_link = f"https://t.me/InvEventBot?start=join_{ev.id}"

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("description", url=desc_link),
        InlineKeyboardButton("join", url=join_link)
    )

    # 6) Send summary (no description text) with inline buttons
    # Build a clickable map link if location_txt contains coordinates "lat,lon"
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
    bot.send_message(user_id, summary, parse_mode="HTML", reply_markup=inline_kb)

    # 7) Reset wizard, go back to main menu
    wiz_reset(user_id)
    # Defer MAIN_KB import to here, not at module top
    from invevent.bot import MAIN_KB
    bot.send_message(user_id, "Event created! Back to main menu.", reply_markup=MAIN_KB)
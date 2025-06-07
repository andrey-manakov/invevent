# wizard/steps/step2_datetime.py

from telebot import types
from datetime import datetime, timezone, timedelta
from ..wizard_utils import EVENT_OPTIONS

def handle(bot, m, w):
    """
    step 2: user tapped “today” or “tomorrow” or “back.”
    """
    user_id = m.from_user.id

    # 1) Back → return to step 1 (event choice)
    if m.text == "back":
        w["step"] = 1
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for o in EVENT_OPTIONS.get(w.get("topic"), []):
            kb.add(o)
        kb.add("back", "cancel")
        bot.send_message(user_id, "Select event type:", reply_markup=kb)
        return

    # 2) “today” / “tomorrow” logic
    now_utc = datetime.now(timezone.utc)
    if m.text == "today":
        w["datetime_utc"] = now_utc
    elif m.text == "tomorrow":
        tomorrow_midnight = (
            now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1)
        )
        w["datetime_utc"] = tomorrow_midnight
    else:
        # invalid input → re‐prompt
        bot.send_message(user_id, "Please tap one of the buttons: “today” or “tomorrow”.")
        return

    # 3) Advance to step 3, ask for location
    w["step"] = 3
    loc_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    loc_kb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
    loc_kb.add(types.KeyboardButton("📌 Pick a location on map (use 📎 → Location)", request_location=False))
    loc_kb.add("back", "cancel")
    bot.send_message(
        user_id,
        "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map,\n"
        "or type a custom address. Use “back” or “cancel” as needed.",
        reply_markup=loc_kb,
    )

# wizard/steps/step3_tags.py

from telebot import types
from ..wizard_utils import TAGS

def handle(bot, m, w):
    """
    step 3: user tapped a tag button or “Other” or “back.”
    """
    user_id = m.from_user.id

    # 1) Back → go to step 2
    if m.text == "back":
        w["step"] = 2
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("today", "tomorrow", "back", "cancel")
        bot.send_message(user_id, "Choose date & time:", reply_markup=kb)
        return

    # 2) Check valid tag
    if m.text in TAGS:
        w["tags"] = [m.text]
    elif m.text == "Other":
        w["tags"] = ["Other"]
    else:
        bot.send_message(user_id, "Please select exactly one of the tag buttons (or “Other”).")
        return

    # 3) Advance to step 4, ask for location via map or text
    w["step"] = 4
    loc_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    loc_kb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
    loc_kb.add(types.KeyboardButton("📌 Pick a location on map (use 📎 → Location)", request_location=False))
    loc_kb.add("back", "cancel")
    bot.send_message(
        user_id,
        "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map, or type an address.",
        reply_markup=loc_kb
    )
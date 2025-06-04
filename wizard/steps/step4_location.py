# wizard/steps/step4_location.py

from telebot import types
from ..wizard_utils import TAGS

def handle(bot, m, w):
    """
    step 4: user tapped “moscow” or “back.” 
    (In the original, only “moscow” was accepted; adjust if you want to accept arbitrary text.)
    """
    user_id = m.from_user.id

    # 1) Back → go to step 3
    if m.text == "back":
        w["step"] = 3
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for t in TAGS:
            kb.add(t)
        kb.add("Other", "back", "cancel")
        bot.send_message(user_id, "Select a tag (one only):", reply_markup=kb)
        return

    # 2) Require exactly “moscow” (case‐sensitive here)
    if m.text != "moscow":
        bot.send_message(
            user_id,
            "Please tap “moscow” to choose the location, or “back”/“cancel”."
        )
        return

    # 3) Store and advance
    w["location_txt"] = "Moscow"
    w["step"] = 5

    vis_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    vis_kb.add("public", "private", "back", "cancel")
    bot.send_message(user_id, "Choose visibility:", reply_markup=vis_kb)
# wizard/steps/step2_datetime.py

from telebot import types
from datetime import datetime, timezone, timedelta
from ..wizard_utils import TAGS

def handle(bot, m, w):
    """
    step 2: user tapped “today” or “tomorrow” or “back.”
    """
    user_id = m.from_user.id

    # 1) Back → go to step 1
    if m.text == "back":
        w["step"] = 1
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        kb.add("default", "back", "cancel")
        bot.send_message(user_id, "Event description?", reply_markup=kb)
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

    # 3) Advance to step 3, ask for tag
    w["step"] = 3
    tag_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for t in TAGS:
        tag_kb.add(t)
    tag_kb.add("Other", "back", "cancel")
    bot.send_message(user_id, "Select a tag (one only):", reply_markup=tag_kb)
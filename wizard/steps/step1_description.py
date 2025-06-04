# wizard/steps/step1_description.py

from telebot import types
from ..wizard_utils import random_suffix

def handle(bot, m, w):
    """
    step 1: user typed description or tapped “default” or “back.”
    """
    user_id = m.from_user.id

    # 1) Back to step 0?
    if m.text == "back":
        w["step"] = 0
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add("default", "cancel")
        bot.send_message(user_id, "Event title?", reply_markup=kb)
        return

    # 2) “default” description
    if m.text == "default":
        w["description"] = f"Description {random_suffix()}"
    else:
        w["description"] = m.text

    # 3) Advance to step 2, ask for date/time
    w["step"] = 2
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("today", "tomorrow", "back", "cancel")
    bot.send_message(user_id, "Choose date & time:", reply_markup=kb)
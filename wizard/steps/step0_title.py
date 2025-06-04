# wizard/steps/step0_title.py

from telebot import types
from ..wizard_utils import random_suffix

def handle(bot, m, w):
    """
    step 0: user just typed or tapped “default” for title.
    → set w["title"], increment to step 1.
    """
    user_id = m.from_user.id

    # 1) “default” → random title; else use raw text
    if m.text == "default":
        w["title"] = f"Event title {random_suffix()}"
    else:
        w["title"] = m.text

    # 2) advance step
    w["step"] = 1

    # 3) ask for description with “default” / “back” / “cancel”
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("default", "back", "cancel")

    bot.send_message(user_id, "Event description?", reply_markup=kb)
# wizard/steps/step1_event.py

from telebot import types
from ..wizard_utils import TOPICS, EVENT_OPTIONS


def handle(bot, m, w):
    """Step 1: choose a specific event based on previously selected topic."""
    user_id = m.from_user.id

    if m.text == "back":
        w["step"] = 0
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(*TOPICS)
        kb.add("cancel")
        bot.send_message(user_id, "Select a topic:", reply_markup=kb)
        return

    options = EVENT_OPTIONS.get(w.get("topic"), [])
    if m.text not in options:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(*options)
        kb.add("back", "cancel")
        bot.send_message(user_id, "Please choose one of the options:", reply_markup=kb)
        return

    w["title"] = m.text
    w["step"] = 2
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("today", "tomorrow", "back", "cancel")
    bot.send_message(user_id, "Choose date & time:", reply_markup=kb)

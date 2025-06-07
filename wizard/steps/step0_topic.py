# wizard/steps/step0_topic.py

from telebot import types
from ..wizard_utils import TOPICS, EVENT_OPTIONS


def handle(bot, m, w):
    """Step 0: choose a topic."""
    user_id = m.from_user.id

    if m.text not in TOPICS:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for t in TOPICS:
            kb.add(t)
        kb.add("cancel")
        bot.send_message(user_id, "Select a topic:", reply_markup=kb)
        return

    w["topic"] = m.text
    w["step"] = 1

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for opt in EVENT_OPTIONS.get(m.text, []):
        kb.add(opt)
    kb.add("back", "cancel")
    bot.send_message(user_id, "Select event type:", reply_markup=kb)

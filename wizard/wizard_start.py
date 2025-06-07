# wizard/wizard_start.py

from telebot import types
from .wizard import start as wiz_start
from .wizard_utils import TOPICS

def register_start(bot):
    """
    Registers the “➕ Create event” entry‐point. 
    Puts user at step 0 (topic selection) and sends the first keyboard.
    """
    @bot.message_handler(func=lambda m: m.text == "➕ Create event")
    def start_event(m):
        user_id = m.from_user.id
        wiz_start(user_id)

        # Keyboard for step 0: list of topics + cancel
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(*TOPICS)
        kb.add("cancel")

        bot.reply_to(m, "Select a topic:", reply_markup=kb)

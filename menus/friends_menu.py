from telebot import types
from .state import set_state

BACK_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
BACK_KB.add("⬅️ Back")


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "👥 Friends")
    def friends_menu(msg):
        set_state(msg.from_user.id, "friends")
        bot.send_message(msg.chat.id, "Friends functionality coming soon.", reply_markup=BACK_KB)


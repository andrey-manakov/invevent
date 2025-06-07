from telebot import types
from ..database import SessionLocal
from ..models import Event, Participation, Friendship, User
from .state import set_state, get_state
from ..demo_data import generate_test_data

SETTINGS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
SETTINGS_KB.add("🗑 Clean the data", "🧪 Generate test data", "⬅️ Back")


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
    def settings_menu(msg):
        set_state(msg.from_user.id, "settings")
        bot.send_message(msg.chat.id, "Settings:", reply_markup=SETTINGS_KB)

    @bot.message_handler(func=lambda m: m.text == "🗑 Clean the data")
    def clean_data(msg):
        with SessionLocal() as db:
            db.query(Participation).delete()
            db.query(Event).delete()
            db.query(Friendship).delete()
            db.query(User).delete()
            db.commit()
        bot.reply_to(msg, "All data have been deleted.")

    @bot.message_handler(func=lambda m: m.text == "🧪 Generate test data")
    def gen_test_data(msg):
        generate_test_data(msg.from_user.id)
        bot.reply_to(msg, "Test data generated.")

    @bot.message_handler(func=lambda m: m.text == "⬅️ Back" and get_state(m.from_user.id) == "settings")
    def back(msg):
        from ..bot import MAIN_KB
        set_state(msg.from_user.id, "main")
        bot.send_message(msg.chat.id, "Main menu:", reply_markup=MAIN_KB)


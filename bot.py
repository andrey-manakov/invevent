
import logging
from telebot import TeleBot, types
from .callbacks import register_callbacks
from .config import BOT_TOKEN, ADMIN_CHAT_ID
from .database import Base, engine
from .menus import register_menu
from .wizard.wizard_start import register_start
from .wizard.wizard_dispatcher import register_dispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="bot.log",
    filemode="a",
)
log=logging.getLogger("invevent")

bot=TeleBot(BOT_TOKEN,parse_mode="HTML")
Base.metadata.create_all(engine)

MAIN_KB=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
MAIN_KB.add(
    "📅 Events",
    "➕ Create event",
    "👥 Friends",
    "⚙️ Settings"
)

# @bot.message_handler(commands=["start"])
# def start(m):
#     bot.send_message(m.chat.id,f"<b>Hi {m.from_user.first_name}!</b>\nPlan, share & join outings. in bot",
#                      parse_mode="HTML",reply_markup=MAIN_KB)

register_menu(bot)
register_start(bot)
register_dispatcher(bot)
register_callbacks(bot)

if ADMIN_CHAT_ID:
    try:
        bot.send_message(ADMIN_CHAT_ID, "Bot started")
    except Exception as e:
        log.warning("Failed to notify startup: %s", e)

def main():
    log.info("Polling...")
    bot.infinity_polling(skip_pending=True,timeout=30)

if __name__=="__main__":
    main()

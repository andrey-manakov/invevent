from telebot import TeleBot, types
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("invevent")

# Initialize bot
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# Define main keyboard
MAIN_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
MAIN_KB.add(
    "📅 My events",
    "🧑‍🤝‍🧑 Friends' events",
    "🌐 Public events",
    "➕ Create event",
    "⚙️ Settings"
)

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        f"<b>Hi {msg.from_user.first_name}!</b>\nPlan, share & join outings.",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )

if __name__ == "__main__":
    log.info("Bot is starting...")
    bot.infinity_polling(skip_pending=True, timeout=30)
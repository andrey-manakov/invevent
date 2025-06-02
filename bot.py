import logging
from telebot import TeleBot
from .config import BOT_TOKEN
from .routes import register_routes

logging.basicConfig(level=logging.INFO)
bot=TeleBot(BOT_TOKEN,parse_mode="HTML")
register_routes(bot)

def main():
    logging.info("Start polling")
    bot.infinity_polling(skip_pending=True,timeout=30)

if __name__=="__main__":
    main()

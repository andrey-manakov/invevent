from telebot import types

def register_routes(bot):

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
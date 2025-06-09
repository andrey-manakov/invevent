# wizard/steps/step5_picture.py

from telebot import types


def handle(bot, m, w):
    """Step 4: optional picture."""
    user_id = m.from_user.id

    if m.text == "back":
        w["step"] = 3
        from .step3_location import handle as step3_handle
        step3_handle(bot, m, w)
        return

    if m.text == "skip":
        w["photo_file_id"] = None
        w["step"] = 5
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        kb.add("skip", "back", "cancel")
        bot.send_message(user_id, "Add a description or tap skip:", reply_markup=kb)
        return

    if m.content_type == "photo" and m.photo:
        w["photo_file_id"] = m.photo[-1].file_id
        w["step"] = 5
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        kb.add("skip", "back", "cancel")
        bot.send_message(user_id, "Add a description or tap skip:", reply_markup=kb)
        return

    # Any other input → re-prompt
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("skip", "back", "cancel")
    bot.send_message(user_id, "Send a picture for the event or tap skip:", reply_markup=kb)

# wizard/steps/step3_tags.py

from telebot import types
from ..wizard_utils import TAGS

def handle(bot, m, w):
    """
    step 3: user has selected a tag. Now advance to step 4 and ask for location.
    We offer two buttons:
      • “Send my current location” → Telegram automatically shares GPS.
      • “Pick a location on map” → user must open the paperclip → Location and drop a pin.
    """

    user_id = m.from_user.id

    # 1) If user tapped “back,” return to step 2 (example: description)
    if m.text == "back":
        w["step"] = 2
        # Re-send whatever keyboard belongs to step 2, e.g.:
        # bot.send_message(user_id, "Step 2 prompt here", reply_markup=step2_kb)
        return

    # 2) If user tapped “cancel,” abort the wizard
    if m.text == "cancel":
        w["step"] = None
        bot.send_message(user_id, "Wizard canceled.", reply_markup=types.ReplyKeyboardRemove())
        return

    # 3) Otherwise, store the chosen tag
    w["tag"] = m.text

    # 4) Advance to step 4, ask for location via map or text
    w["step"] = 4
    loc_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    loc_kb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
    loc_kb.add(types.KeyboardButton("📌 Pick a location on map (use 📎 → Location)", request_location=False))
    loc_kb.add("back", "cancel")

    bot.send_message(
        user_id,
        "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map,\n"
        "or type a custom address. Use “back” or “cancel” as needed.",
        reply_markup=loc_kb
    )
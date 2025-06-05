# wizard/steps/step4_location.py

from telebot import types

PICK_ON_MAP_LABEL = "📌 Pick a location on map (use 📎 → Location)"

def handle(bot, m, w):
    """
    step 4: prompt user to share location via map (GPS) or type an address.
    """

    user_id = m.from_user.id

    # 1) If it's not step 4, do nothing
    if w.get("step") != 4:
        return

    # 2) If a Location object arrived, save coords and advance
    if m.content_type == 'location' and m.location is not None:
        lat = m.location.latitude
        lon = m.location.longitude

        w["latitude"] = lat
        w["longitude"] = lon
        w["address"] = None

        bot.send_message(
            user_id,
            "✅ Got it! Location is saved.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        w["step"] = 5
        vis_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        vis_kb.add("public", "private", "back", "cancel")
        bot.send_message(user_id, "Choose visibility:", reply_markup=vis_kb)
        return

    # 3) If user tapped “back,” go back to step 3 (tags)
    if m.text == "back":
        w["step"] = 3
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        from ..wizard_utils import TAGS
        for t in TAGS:
            kb.add(t)
        kb.add("Other", "back", "cancel")
        bot.send_message(user_id, "Select a tag (one only):", reply_markup=kb)
        return

    # 4) If user tapped “cancel,” abort the wizard
    if m.text == "cancel":
        w["step"] = None
        bot.send_message(user_id, "Wizard canceled.", reply_markup=types.ReplyKeyboardRemove())
        return

    # 5) If user tapped the “Pick on map” button (it sends that exact text), show instructions
    if m.text == PICK_ON_MAP_LABEL:
        bot.send_message(
            user_id,
            "Чтобы выбрать точку на карте, нажмите на значок 📎 (скрепку) → «Location» и выберите нужную точку."
        )
        return

    # 6) If user typed any other text, treat it as a free-text address and advance
    if m.text is not None:
        address_str = m.text.strip()
        w["address"] = address_str
        w["latitude"] = None
        w["longitude"] = None

        bot.send_message(
            user_id,
            f"✅ Understood—we’ll use “{address_str}” as the event address.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        w["step"] = 5
        vis_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        vis_kb.add("public", "private", "back", "cancel")
        bot.send_message(user_id, "Choose visibility:", reply_markup=vis_kb)
        return

    # 7) If none of the above (e.g. first entry to step 4), send the “share/pick location” keyboard
    rb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    rb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
    rb.add(types.KeyboardButton(PICK_ON_MAP_LABEL, request_location=False))
    rb.add("back", "cancel")

    bot.send_message(
        user_id,
        "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map,\n"
        "or type a custom address. Use “back” or “cancel” as needed.",
        reply_markup=rb
    )
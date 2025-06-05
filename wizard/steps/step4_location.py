from telebot import types

def handle(bot, m, w):
    """
    step 4: prompt user to share location via map (GPS).
    If they tap “Send my current location,” Telegram returns a Location object.
    Fallback: if they send text instead, treat it as a free-text address.
    """

    user_id = m.from_user.id

    # 1) If user tapped “back,” go back to step 3 (tags)
    if m.text == "back":
        w["step"] = 3
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        from ..wizard_utils import TAGS
        for t in TAGS:
            kb.add(t)
        kb.add("Other", "back", "cancel")
        bot.send_message(user_id, "Select a tag (one only):", reply_markup=kb)
        return

    # 2) If user tapped “cancel,” abort the wizard entirely
    if m.text == "cancel":
        w["step"] = None
        bot.send_message(user_id, "Wizard canceled.", reply_markup=types.ReplyKeyboardRemove())
        return

    # 3) If we are still in the “ASK_LOCATION” state, send a location-request button
    #    (This button sends the user's current GPS. To pick another point on the map,
    #     instruct users to attach a location manually via the paperclip icon.)
    if w["step"] == 4 and m.location is None:
        rb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        rb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
        rb.add(types.KeyboardButton("📌 Pick a location on map (use 📎 → Location)", request_location=False))
        rb.add("back", "cancel")
        bot.send_message(
            user_id,
            "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map.\n"
            "Use “back” or “cancel” as needed.",
            reply_markup=rb
        )
        return

    # 4) Handle the Location object (user shared a location, either current or picked)
    if m.location is not None and w["step"] == 4:
        lat = m.location.latitude
        lon = m.location.longitude

        # Store latitude/longitude in wizard context
        w["latitude"] = lat
        w["longitude"] = lon
        # Clear any previous free-text address
        w["address"] = None

        # Remove the custom keyboard and advance to visibility step
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

    # 5) Fallback: if user sends free-text instead of a Location object
    if w["step"] == 4 and m.text is not None:
        # Ignore the “Pick a location on map” button press (no payload)
        if m.text == "📌 Pick a location on map (use 📎 → Location)":
            bot.send_message(
                user_id,
                "Чтобы выбрать точку на карте, нажмите на значок 📎 (скрепку) → «Location» и выберите нужную точку."
            )
            return

        address_str = m.text.strip()
        w["address"] = address_str
        # Clear any previously stored coordinates
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

    # 6) Defensive catch: if none of the above matched, re-prompt in step 4
    if w["step"] == 4:
        bot.send_message(
            user_id,
            "Please tap “📍 Send my current location” to share your GPS location, "
            "or type an address. Use “back” or “cancel” as needed."
        )
        return

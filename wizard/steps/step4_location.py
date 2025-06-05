from telebot import types

def handle(bot, m, w):
    """
    step 4: prompt user to share location via map (GPS) or type an address.
    """

    user_id = m.from_user.id

    # 1) Back → step 3 (tags)
    if m.text == "back" and w.get("step") == 4:
        w["step"] = 3
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        from ..wizard_utils import TAGS
        for t in TAGS:
            kb.add(t)
        kb.add("Other", "back", "cancel")
        bot.send_message(user_id, "Select a tag (one only):", reply_markup=kb)
        return

    # 2) Cancel → abort wizard
    if m.text == "cancel" and w.get("step") == 4:
        w["step"] = None
        bot.send_message(user_id, "Wizard canceled.", reply_markup=types.ReplyKeyboardRemove())
        return

    # Only handle step 4 here
    if w.get("step") != 4:
        return

    # 3) If a Location object arrived, save coords and advance
    if hasattr(m, 'location') and m.location is not None:
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

    # 4) If not a location update, re-send the “share/pick location” keyboard
    if m.content_type != 'location':
        rb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        rb.add(types.KeyboardButton("📍 Send my current location", request_location=True))
        rb.add(types.KeyboardButton("📌 Pick a location on map (use 📎 → Location)", request_location=False))
        rb.add("back", "cancel")

        bot.send_message(
            user_id,
            "📍 Tap “Send my current location” or click the 📎 (paperclip) → Location to pick any point on the map.\n"
            "Or type a custom address. Use “back” or “cancel” as needed.",
            reply_markup=rb
        )
        return

    # 5) Fallback: if it’s text (and not the special “pick on map” button), treat as address
    if m.text is not None:
        if m.text == "📌 Pick a location on map (use 📎 → Location)":
            bot.send_message(
                user_id,
                "Чтобы выбрать точку на карте, нажмите на значок 📎 (скрепку) → «Location» и выберите нужную точку."
            )
            return

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

    # 6) If none of the above (e.g. sticker/image), re-prompt
    bot.send_message(
        user_id,
        "Please tap “📍 Send my current location” to share your GPS location,\n"
        "or click the 📎 (paperclip) → Location to pick any point on the map,\n"
        "or type an address. Use “back” or “cancel” as needed."
    )

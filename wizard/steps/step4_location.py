# wizard/steps/step4_location.py

from telebot import types
from ..wizard_utils import TAGS

def handle(bot, m, w):
    """
    step 4: prompt user to share their location via map (GPS).
    If they tap “Send location,” Telegram returns a Location object.
    Fallback: if they send text instead, treat it as a free-text address.
    """

    user_id = m.from_user.id

    # 1) If user tapped “back,” go back to step 3 (choose a tag)
    if m.text == "back":
        w["step"] = 3
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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
    if w["step"] == 4 and not hasattr(m, 'location'):
        # Build a keyboard with a single “Send my location” button
        rb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        rb.add(types.KeyboardButton("📍 Send my location on map", request_location=True))
        rb.add("back", "cancel")
        bot.send_message(
            user_id,
            "📍 Please tap the button below and share your location on the map.",
            reply_markup=rb
        )
        # Stay in step 4 until we receive a Location or text fallback
        return

    # 4) If we received a Location object (user tapped the map button)
    if hasattr(m, 'location') and w["step"] == 4:
        lat = m.location.latitude
        lon = m.location.longitude

        # Store latitude/longitude in wizard context
        w["latitude"] = lat
        w["longitude"] = lon
        # Clear any previous free-text address
        w["address"] = None

        # Remove the custom keyboard
        bot.send_message(
            user_id,
            "✅ Got it! Location is saved.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Advance to step 5 (visibility)
        w["step"] = 5
        vis_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        vis_kb.add("public", "private", "back", "cancel")
        bot.send_message(user_id, "Choose visibility:", reply_markup=vis_kb)
        return

    # 5) Fallback: if user sends text instead of location
    if w["step"] == 4 and isinstance(m.text, str):
        address_str = m.text.strip()
        w["address"] = address_str
        # Clear any previous coordinates
        w["latitude"] = None
        w["longitude"] = None

        bot.send_message(
            user_id,
            f"✅ Understood—we’ll use “{address_str}” as the event address.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Advance to step 5 (visibility)
        w["step"] = 5
        vis_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        vis_kb.add("public", "private", "back", "cancel")
        bot.send_message(user_id, "Choose visibility:", reply_markup=vis_kb)
        return

    # 6) Defensive catch: if none of the above matched, re-prompt
    if w["step"] == 4:
        bot.send_message(
            user_id,
            "Please tap “📍 Send my location on map” to share your GPS location, or type an address. Use “back” or “cancel” as needed."
        )
        return

# wizard/steps/step4_visibility.py

from telebot import types
from invevent.models import EventVisibility

def handle(bot, m, w):
    """
    step 4: user tapped “public” or “private” or “back.”
    Store visibility and move on to the picture step.
    """
    user_id = m.from_user.id

    # 1) Back → return to step 3 (location)
    if m.text == "back":
        w["step"] = 3
        from .step3_location import handle as step3_handle
        # Re-invoke step3 handler to re-send the map/text location keyboard
        step3_handle(bot, m, w)
        return

    # 2) Must be “public” or “private”
    if m.text not in ("public", "private"):
        bot.send_message(
            user_id,
            "Please tap “public”, “private”, “back”, or “cancel”."
        )
        return

    # 3) Store visibility enum
    w["visibility"] = (
        EventVisibility.Public
        if m.text == "public"
        else EventVisibility.Private
    )

    # 4) Advance to step 5 and ask for a picture
    w["step"] = 5
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("skip", "back", "cancel")
    bot.send_message(user_id, "Send a picture for the event or tap skip:", reply_markup=kb)

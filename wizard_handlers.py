"""Full create‑event wizard handlers"""
import uuid
from datetime import datetime, timezone
from telebot import types
from .wizard import STEPS, start as wiz_start, get as wiz_get, reset as wiz_reset, snippet
from .models import Event, EventVisibility
from .database import SessionLocal
TAGS = ["🎉 Party","🎮 Gaming","🍽️ Food","🎬 Cinema"]

def register_wizard(bot):

    # ——— STEP 0: Start dialog (ask for title) ———
    @bot.message_handler(func=lambda m: m.text == "➕ Create event")
    def start(m):
        wiz_start(m.from_user.id)
        # Reply with “Title?” and a keyboard [ “default”, “cancel” ]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add("default", "cancel")
        bot.reply_to(m, "Event title?", reply_markup=kb)

    #
    # ——— UNIVERSAL WIZARD HANDLER: catch all messages while in a wizard state ———
    @bot.message_handler(func=lambda m: wiz_get(m.from_user.id) is not None)
    def _wizard_steps(m):
        user_id = m.from_user.id
        w = wiz_get(user_id)
        step = w["step"]

        # Cancel at any step
        if m.text == "cancel":
            wiz_reset(user_id)
            from .bot import MAIN_KB
            bot.send_message(user_id, "Operation cancelled. Back to main menu.", reply_markup=MAIN_KB)
            return

        # Step 0: Title
        if step == 0:
            if m.text == "default":
                # random suffix for title
                rnd = uuid.uuid4().hex[:4]
                w["title"] = f"Event title {rnd}"
            else:
                # any other text is treated as custom title
                w["title"] = m.text
            # advance
            w["step"] = 1
            # Ask for description
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            kb.add("default", "back", "cancel")
            bot.send_message(user_id, "Event description?", reply_markup=kb)
            return

        # Step 1: Description
        if step == 1:
            if m.text == "back":
                w["step"] = 0
                # Go back to title
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                kb.add("default", "cancel")
                bot.send_message(user_id, "Event title?", reply_markup=kb)
                return
            if m.text == "default":
                rnd = uuid.uuid4().hex[:4]
                w["description"] = f"Description {rnd}"
            else:
                w["description"] = m.text
            # advance
            w["step"] = 2
            # Ask for date & time
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            kb.add("today", "tomorrow", "back", "cancel")
            bot.send_message(user_id, "Choose date & time:", reply_markup=kb)
            return

        # Step 2: Date & time
        if step == 2:
            if m.text == "back":
                w["step"] = 1
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                kb.add("default", "back", "cancel")
                bot.send_message(user_id, "Event description?", reply_markup=kb)
                return
            now_utc = datetime.now(timezone.utc)
            if m.text == "today":
                w["datetime_utc"] = now_utc
            elif m.text == "tomorrow":
                w["datetime_utc"] = now_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                bot.send_message(user_id, "Please tap one of the buttons: “today” or “tomorrow”.")
                return
            # advance
            w["step"] = 3
            # Ask for tag (only one)
            tag_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for t in TAGS:
                tag_kb.add(t)
            tag_kb.add("Other", "back", "cancel")
            bot.send_message(user_id, "Select a tag (one only):", reply_markup=tag_kb)
            return

        # Step 3: Tag
        if step == 3:
            if m.text == "back":
                w["step"] = 2
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                kb.add("today", "tomorrow", "back", "cancel")
                bot.send_message(user_id, "Choose date & time:", reply_markup=kb)
                return
            if m.text in TAGS:
                w["tags"] = [m.text]
            elif m.text == "Other":
                w["tags"] = ["Other"]
            else:
                bot.send_message(user_id, "Please select exactly one of the tag buttons (or “Other”).")
                return
            # advance
            w["step"] = 4
            # Ask for location
            loc_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            loc_kb.add("moscow", "save", "back", "cancel")
            bot.send_message(user_id, "Location? (type a custom place or tap a button)", reply_markup=loc_kb)
            return

        # Step 4: Location
        if step == 4:
            # If user tapped “back”
            if m.text == "back":
                w["step"] = 3
                tag_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for t in TAGS:
                    tag_kb.add(t)
                tag_kb.add("Other", "back", "cancel")
                bot.send_message(user_id, "Select a tag (one only):", reply_markup=tag_kb)
                return

            # If user tapped “moscow” → finalize immediately
            if m.text == "moscow":
                w["location_txt"] = "Moscow"
            # If user tapped “save” → only valid if they already sent free‐text location
            elif m.text == "save":
                if "location_txt_input" not in w:
                    bot.send_message(user_id, "Please type your custom location first, or tap “moscow”.")
                    return
                w["location_txt"] = w.pop("location_txt_input")
            else:
                # any other text is taken as “free‐text location draft”
                w["location_txt_input"] = m.text
                bot.send_message(user_id, "Saved your text. Now tap “save” to confirm, or “moscow” for Moscow.")
                return

            # All required fields are now in w: title, description, datetime_utc, tags, location_txt.
            # Create the Event object and show brief info (no description), plus a deeplink.
            with SessionLocal() as db:
                ev = Event(
                    id=str(uuid.uuid4()),
                    owner_id=user_id,
                    title=w["title"],
                    description=w["description"],
                    datetime_utc=w["datetime_utc"],
                    location_txt=w["location_txt"],
                    visibility=EventVisibility.Public,  # or default as needed
                    tags=",".join(w.get("tags", []))
                )
                db.add(ev)
                db.commit()

            # Send brief confirmation (no description) + deeplink
            # Replace <YourBotUsername> with your actual bot username
            link = f"https://t.me/<YourBotUsername>?start={ev.id}"
            text = (
                f"<b>{w['title']}</b>\n"
                f"🗓️ {w['datetime_utc']:%Y-%m-%d %H:%M UTC}\n"
                f"📍 {w['location_txt']}\n"
                f"🔗 {link}"
            )
            bot.send_message(user_id, text, parse_mode="HTML")

            # Reset wizard and return to main menu
            wiz_reset(user_id)
            from .bot import MAIN_KB
            bot.send_message(user_id, "Event created! Back to main menu.", reply_markup=MAIN_KB)
            return
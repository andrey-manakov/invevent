"""
Simple Telegram Event Bot using pyTelegramBotAPI (telebot) + SQLite.

New in this version (sharing support):
-------------------------------------------------
- /share_event <id> [<user_id|@username>] : send an invite link or direct DM to a contact ⚡️
- Deep‑link handling – a user opening https://t.me/<bot_username>?start=join_<id> joins instantly.
- Help message updated to include /share_event.

Existing commands:
- /start                     : shows help message (or auto‑join via deep‑link)
- /create_event <title>      : create a new event with a title
- /join_event <id>           : join an existing event
- /events                    : list recent events
- /my_events                 : list events you created

Run locally with long‑polling for ease of testing.

Configuration notes:
- Put your Telegram API token as `BOT_TOKEN=<token>` in a file **one directory up** from this script (i.e., `../.env`).
- Requires `python-dotenv` for loading the .env file.

Next steps (ideas):
- Add description/date fields (multi‑step conversation)
- Inline "Join" buttons for nicer UX
- /event <id> command for event details & participant list
- Command to delete/cancel event by creator
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import telebot
from telebot.types import Message

# --- Configuration ---------------------------------------------------------
# Load BOT_TOKEN from ../.env (parent directory of this file)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN not set. Add BOT_TOKEN=<your_token> to ../.env or export it as env var."
    )

DB_PATH = "events.db"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Cache bot username once so we can build deep‑links
BOT_USERNAME: str = bot.get_me().username

# --- Database helpers ------------------------------------------------------

def init_db() -> None:
    """Create tables if they do not yet exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            title TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            event_id INTEGER,
            user_id INTEGER,
            joined_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, user_id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_event_title(event_id: int) -> Optional[str]:
    """Return event title for given id or None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title FROM events WHERE id = ?", (event_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


init_db()

# --- Command handlers ------------------------------------------------------


def help_text() -> str:
    return (
        "👋 <b>Hi!</b> I can help you organise simple events.\n\n"
        "Commands:\n"
        "/create_event &lt;title&gt;  – create a new event\n"
        "/join_event &lt;id&gt;       – join an event\n"
        "/share_event &lt;id&gt; [user] – invite a friend\n"
        "/events                – list recent events\n"
        "/my_events             – list events you created"
    )


@bot.message_handler(commands=["start"])
def cmd_start(message: Message):
    """Show help or join via deep‑link."""
    args = message.text.split(maxsplit=1)

    # Deep‑link: /start join_<id>
    if len(args) == 2 and args[1].startswith("join_") and args[1][5:].isdigit():
        # Re‑use existing join logic
        fake_join_msg = message
        fake_join_msg.text = f"/join_event {args[1][5:]}"
        cmd_join_event(fake_join_msg)
        return

    bot.reply_to(message, help_text())


@bot.message_handler(commands=["create_event"])
def cmd_create_event(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /create_event <title>")
        return

    title = args[1].strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (creator_id, title) VALUES (?, ?)",
        (message.from_user.id, title),
    )
    event_id = c.lastrowid
    conn.commit()
    conn.close()

    deep_link = f"https://t.me/{BOT_USERNAME}?start=join_{event_id}"

    bot.reply_to(
        message,
        (
            f"✅ Event #{event_id} created!\n"
            f"Title: <b>{title}</b>\n\n"
            "Ask friends to join using one of these: \n"
            f"• <code>/join_event {event_id}</code> (copy)\n"
            f"• {deep_link} (tap to open)\n\n"
            f"Or send <code>/share_event {event_id}</code> to quickly forward an invite."
        ),
        disable_web_page_preview=True,
    )


@bot.message_handler(commands=["share_event"])
def cmd_share_event(message: Message):
    """Let an organiser quickly share an invite."""
    args = message.text.split(maxsplit=2)
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Usage: /share_event <event_id> [<user_id|@username>]")
        return

    event_id = int(args[1])
    title = get_event_title(event_id)
    if title is None:
        bot.reply_to(message, "❌ Event not found.")
        return

    deep_link = f"https://t.me/{BOT_USERNAME}?start=join_{event_id}"
    invite_text = (
        f"📨 <b>Invitation</b>\n"
        f"You have been invited to <b>{title}</b> (#{event_id}).\n"
        f"Tap to join ➡️ {deep_link} or send /join_event {event_id}."
    )

    # If a recipient is provided, try DM‑ing them directly.
    if len(args) == 3:
        recipient = args[2].strip()
        # Numeric user ID?
        if recipient.isdigit():
            try:
                bot.send_message(int(recipient), invite_text, disable_web_page_preview=True)
                bot.reply_to(message, "✅ Invite sent via DM!")
            except telebot.apihelper.ApiTelegramException:
                bot.reply_to(message, "⚠️ Couldn't deliver – has the user started the bot?")
        else:
            # Assume @username – bots cannot DM unless user started them, so just send text back.
            bot.reply_to(
                message,
                f"Forward this to {recipient}:\n\n{invite_text}",
                disable_web_page_preview=True,
            )
    else:
        # No recipient – just show invite text so user can forward.
        bot.reply_to(message, invite_text, disable_web_page_preview=True)


@bot.message_handler(commands=["join_event"])
def cmd_join_event(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Usage: /join_event <event_id>")
        return

    event_id = int(args[1])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT title FROM events WHERE id = ?", (event_id,))
    row = c.fetchone()
    if row is None:
        bot.reply_to(message, "❌ Event not found.")
        conn.close()
        return

    try:
        c.execute(
            "INSERT INTO participants (event_id, user_id) VALUES (?, ?)",
            (event_id, message.from_user.id),
        )
        conn.commit()
        bot.reply_to(message, f"🎉 You joined event #{event_id}: <b>{row[0]}</b>")
    except sqlite3.IntegrityError:
        bot.reply_to(message, "ℹ️ You have already joined this event.")
    finally:
        conn.close()


@bot.message_handler(commands=["events"])
def cmd_events(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, title, ts FROM events ORDER BY ts DESC LIMIT 20"
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "No events yet. Create one with /create_event!")
        return

    lines = ["📅 <b>Recent events</b>:"]
    for eid, title, ts in rows:
        lines.append(f"{eid}. {title} (created {ts})")
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["my_events"])
def cmd_my_events(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, title, ts
        FROM events
        WHERE creator_id = ?
        ORDER BY ts DESC
        """,
        (message.from_user.id,),
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "You haven't created any events yet.")
        return

    lines = ["🗓️ <b>Your events</b>:"]
    for eid, title, ts in rows:
        lines.append(f"{eid}. {title} (created {ts})")
    bot.reply_to(message, "\n".join(lines))


# --- Main loop -------------------------------------------------------------
if __name__ == "__main__":
    print("Bot is running… Press Ctrl+C to stop.")
    bot.infinity_polling()

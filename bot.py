"""
Simple Telegram Event Bot using pyTelegramBotAPI (telebot) + SQLite.

Features implemented so far:
- /start             : shows help message
- /create_event      : create a new event with a title
- /join_event <id>   : join an existing event
- /events            : list recent events
- /my_events         : list events you created

Run locally with long‑polling for ease of testing.
Set BOT_TOKEN as an environment variable or replace the placeholder below.

Next steps (ideas):
- Add description/date fields (multi‑step conversation)
- Inline "Join" buttons for nicer UX
- /event <id> command for event details & participant list
- Command to delete/cancel event by creator
"""

import os
import sqlite3
import telebot
from telebot.types import Message

# --- Configuration ---------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_PATH = "events.db"

bot = telebot.TeleBot(BOT_TOKEN)

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


init_db()

# --- Command handlers ------------------------------------------------------


@bot.message_handler(commands=["start"])
def cmd_start(message: Message):
    bot.reply_to(
        message,
        (
            "👋 Hi, I can help you organize simple events!\n\n"
            "Commands:\n"
            "/create_event <title>  – create a new event\n"
            "/join_event <id>      – join an event\n"
            "/events               – list recent events\n"
            "/my_events            – list events you created"
        ),
    )


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

    bot.reply_to(
        message,
        (
            f"✅ Event #{event_id} created!\n"
            f"Title: {title}\n\n"
            "Share this command so friends can join: \n"
            f"/join_event {event_id}"
        ),
    )


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
        bot.reply_to(message, f"🎉 You joined event #{event_id}: {row[0]}")
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

    lines = ["📅 Recent events:"]
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

    lines = ["🗓️ Your events:"]
    for eid, title, ts in rows:
        lines.append(f"{eid}. {title} (created {ts})")
    bot.reply_to(message, "\n".join(lines))


# --- Main loop -------------------------------------------------------------
if __name__ == "__main__":
    print("Bot is running… Press Ctrl+C to stop.")
    bot.infinity_polling()
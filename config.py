"""App configuration (loads .env)."""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DB_URL: str = os.getenv("DB_URL", "sqlite:///db.sqlite3")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment (.env)")

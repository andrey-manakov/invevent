import os
from pathlib import Path
from dotenv import load_dotenv

# Try .env in project root or one level up
for p in [Path(__file__).resolve().parents[1] / ".env",
          Path(__file__).resolve().parents[2] / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL", "sqlite:///db.sqlite3")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

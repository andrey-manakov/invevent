"""App configuration (loads .env)."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Look for .env in project root *or* one level above (handy for monorepos)
candidate_paths = [
    Path(__file__).resolve().parents[1] / ".env",  # project root
    Path(__file__).resolve().parents[2] / ".env",  # parent folder
]
for p in candidate_paths:
    if p.exists():
        load_dotenv(p)
        break

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DB_URL: str = os.getenv("DB_URL", "sqlite:///db.sqlite3")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment (.env)")

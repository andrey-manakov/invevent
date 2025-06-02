import os, pathlib
from dotenv import load_dotenv

for p in [pathlib.Path(__file__).resolve().parents[1]/".env",
          pathlib.Path(__file__).resolve().parents[2]/".env"]:
    if p.exists():
        load_dotenv(p)
        break

BOT_TOKEN=os.getenv("BOT_TOKEN")
DB_URL=os.getenv("DB_URL","sqlite:///db.sqlite3")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

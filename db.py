import aiosqlite, pathlib, asyncio
DB_PATH = pathlib.Path("./invevent.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  last_loc_lat REAL,
  last_loc_lon REAL
);
CREATE TABLE IF NOT EXISTS friend_links(
  user_id INTEGER,
  friend_id INTEGER,
  PRIMARY KEY (user_id, friend_id)
);
CREATE TABLE IF NOT EXISTS friend_requests(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_id INTEGER,
  to_id INTEGER,
  status TEXT
);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER,
  title TEXT,
  dt_utc TEXT,
  lat REAL,
  lon REAL,
  location_text TEXT,
  tags TEXT
);
CREATE TABLE IF NOT EXISTS attendees(
  event_id INTEGER,
  user_id INTEGER,
  PRIMARY KEY (event_id, user_id)
);
"""

async def get_db():
    return await aiosqlite.connect(DB_PATH)

async def init_db():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    await conn.commit()
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init_db())
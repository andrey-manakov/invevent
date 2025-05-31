import asyncio, os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from routers.start import router as start_router
from routers.events import router as events_router
from routers.friends import router as friends_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the environment")

async def main() -> None:
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(events_router)
    dp.include_router(friends_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio, os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from routers.start import router as start_router
from routers.events import router as events_router
from routers.friends import router as friends_router

BOT_TOKEN = os.getenv("BOT_TOKEN", "CHANGE_ME")

async def main() -> None:
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(events_router)
    dp.include_router(friends_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
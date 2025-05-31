from aiogram import Router, types, F
from aiogram.filters import CommandStart
from db import get_db

router = Router()

WELCOME_KB = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[[types.KeyboardButton(text="📅 My events"), types.KeyboardButton(text="➕ Create event")],
             [types.KeyboardButton(text="👥 Friends"), types.KeyboardButton(text="📍 Nearby")]]
)

@router.message(CommandStart())
async def start(msg: types.Message):
    # register user if first time
    async with await get_db() as db:
        await db.execute("INSERT OR IGNORE INTO users(id, username, first_name, last_name) VALUES(?,?,?,?)",
                         (msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.from_user.last_name))
        await db.commit()
    await msg.answer("👋 Welcome to Invevent Bot!", reply_markup=WELCOME_KB)
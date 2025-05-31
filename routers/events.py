from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from db import get_db
from datetime import datetime

router = Router()

class CreateEvent(StatesGroup):
    title = State()
    dt = State()
    location = State()
    tags = State()

@router.message(F.text == "➕ Create event")
async def create_event(msg: types.Message, state: FSMContext):
    await state.set_state(CreateEvent.title)
    await msg.answer("📝 Event title?")

@router.message(CreateEvent.title)
async def got_title(msg: types.Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await state.set_state(CreateEvent.dt)
    await msg.answer("⏰ Date & time (YYYY‑MM‑DD HH:MM)?")

@router.message(CreateEvent.dt)
async def got_dt(msg: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
    except ValueError:
        return await msg.answer("❌ Format invalid. Try YYYY‑MM‑DD HH:MM")
    await state.update_data(dt=dt.isoformat())
    await state.set_state(CreateEvent.location)
    await msg.answer("📍 Send location", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Share location", request_location=True)]], resize_keyboard=True, one_time_keyboard=True))

@router.message(CreateEvent.location, F.location)
async def got_location(msg: types.Message, state: FSMContext):
    await state.update_data(lat=msg.location.latitude, lon=msg.location.longitude)
    await state.set_state(CreateEvent.tags)
    await msg.answer("🏷 Choose tag:", reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="🎭 Culture", callback_data="TAG_culture"),
                          types.InlineKeyboardButton(text="⚽ Sport", callback_data="TAG_sport")],
                         [types.InlineKeyboardButton(text="🍻 Hang out", callback_data="TAG_hangout"),
                          types.InlineKeyboardButton(text="💼 Work", callback_data="TAG_work")],
                         [types.InlineKeyboardButton(text="🥂 Drinking", callback_data="TAG_drinking")]]))

@router.callback_query(F.data.startswith("TAG_"))
async def save_event(cb: types.CallbackQuery, state: FSMContext):
    tag = cb.data[4:]
    data = await state.get_data()
    async with await get_db() as db:
        await db.execute("INSERT INTO events(owner_id,title,dt_utc,lat,lon,tags) VALUES(?,?,?,?,?,?)",
                         (cb.from_user.id, data["title"], data["dt"], data["lat"], data["lon"], tag))
        await db.commit()
    await state.clear()
    await cb.message.edit_text("✅ Event saved!")
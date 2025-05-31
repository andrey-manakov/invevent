from aiogram import Router, types, F
from db import get_db

router = Router()

@router.message(F.text == "👥 Friends")
async def friends_menu(msg: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Add friend", switch_inline_query="invite_me")],
        [types.InlineKeyboardButton(text="📥 Requests", callback_data="SHOW_REQ")]
    ])
    await msg.answer("Friends menu:", reply_markup=kb)

@router.inline_query()
async def invite_inline(iq: types.InlineQuery):
    # Return deep‑link instruction
    await iq.answer(results=[], switch_pm_text="Tap to open bot", switch_pm_parameter=f"invite_{iq.from_user.id}")

@router.message(F.text == "📅 My events")
async def my_events(msg: types.Message):
    async with await get_db() as db:
        rows = await db.execute_fetchall("SELECT id,title,dt_utc FROM events WHERE owner_id=?", (msg.from_user.id,))
    if not rows:
        return await msg.answer("No events yet.")
    reply = "Your events:\n" + "\n".join(f"{r['id']}. {r['title']} at {r['dt_utc'][:16]}" for r in rows)
    await msg.answer(reply)
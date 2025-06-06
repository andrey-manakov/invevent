from io import BytesIO
from telebot import types
from staticmap import StaticMap, CircleMarker
from staticmap.staticmap import _lon_to_x, _lat_to_y
from PIL import ImageDraw, ImageFont
from .helpers import cb


def show_events_on_map(bot, chat_id: int, events):
    """Display all given events on a single map with detail buttons."""

    evs = [e for e in events if e.latitude is not None and e.longitude is not None]
    if not evs:
        bot.send_message(chat_id, "No events with location to show.")
        return

    m = StaticMap(600, 400)
    for e in evs:
        m.add_marker(CircleMarker((e.longitude, e.latitude), "#d33", 12))

    img = m.render()
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    for idx, e in enumerate(evs, start=1):
        x = m._x_to_px(_lon_to_x(e.longitude, m.zoom))
        y = m._y_to_px(_lat_to_y(e.latitude, m.zoom))
        draw.text((x + 6, y - 12), str(idx), fill="black", font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    kb = types.InlineKeyboardMarkup(row_width=2)
    for idx, e in enumerate(evs, start=1):
        kb.add(types.InlineKeyboardButton(f"{idx}. {e.title}", callback_data=cb(e.id, "summary")))

    bot.send_photo(chat_id, buf, reply_markup=kb)

from io import BytesIO
import logging
from telebot import types
from staticmap import StaticMap, CircleMarker
from staticmap.staticmap import _lon_to_x, _lat_to_y
from PIL import ImageDraw, ImageFont
import folium
import requests

from .helpers import cb

log = logging.getLogger(__name__)


def _geocode_address(address: str):
    """Return (lat, lon) for address using OpenStreetMap Nominatim."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "invevent-bot"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:  # pragma: no cover - network failures
        log.warning("Geocoding failed for '%s': %s", address, e)
    return None


def show_events_on_map(bot, chat_id: int, events):
    """Display all given events on a single map with detail buttons."""

    evs = []
    for e in events:
        lat = e.latitude
        lon = e.longitude
        if lat is None or lon is None:
            if e.address:
                coords = _geocode_address(e.address)
                if coords:
                    lat, lon = coords
        if lat is not None and lon is not None:
            evs.append((e, lat, lon))

    if not evs:
        bot.send_message(chat_id, "No events with location to show.")
        return

    m = StaticMap(600, 400)
    for e, lat, lon in evs:
        m.add_marker(CircleMarker((lon, lat), "#d33", 12))

    img = m.render()
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    for idx, (e, lat, lon) in enumerate(evs, start=1):
        x = m._x_to_px(_lon_to_x(lon, m.zoom))
        y = m._y_to_px(_lat_to_y(lat, m.zoom))
        draw.text((x + 6, y - 12), str(idx), fill="black", font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    kb = types.InlineKeyboardMarkup(row_width=2)
    for idx, (e, _lat, _lon) in enumerate(evs, start=1):
        kb.add(types.InlineKeyboardButton(f"{idx}. {e.title}", callback_data=cb(e.id, "summary")))

    bot.send_photo(chat_id, buf, reply_markup=kb)


def show_events_interactive_map(bot, chat_id: int, events):
    """Send an interactive HTML map with markers for each event."""

    evs = []
    for e in events:
        lat = e.latitude
        lon = e.longitude
        if lat is None or lon is None:
            if e.address:
                coords = _geocode_address(e.address)
                if coords:
                    lat, lon = coords
        if lat is not None and lon is not None:
            evs.append((e, lat, lon))

    if not evs:
        bot.send_message(chat_id, "No events with location to show.")
        return

    first_lat, first_lon = evs[0][1], evs[0][2]
    m = folium.Map(location=[first_lat, first_lon], zoom_start=12)

    for e, lat, lon in evs:
        popup_text = (
            f"<b>{e.title}</b><br>"
            f"{e.datetime_utc:%Y-%m-%d %H:%M UTC}<br>"
            f"{e.location_txt or ''}"
        )
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
        ).add_to(m)

    html = m.get_root().render()
    buf = BytesIO(html.encode("utf-8"))
    buf.name = "events_map.html"

    bot.send_document(
        chat_id,
        buf,
        caption="Open this file to view the interactive map.",
    )

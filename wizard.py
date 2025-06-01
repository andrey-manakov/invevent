"""Simple in‑memory wizard state per user."""
from datetime import datetime, timezone
from typing import Dict, Any

MAX_SNIPPET = 200
STEPS = ["title", "description", "datetime", "tags", "location", "visibility", "confirm"]

WIZ: Dict[int, Dict[str, Any]] = {}

def reset(uid: int):
    WIZ.pop(uid, None)

def start(uid: int):
    reset(uid)
    WIZ[uid] = {"step": 0}

def get(uid: int):
    return WIZ.get(uid)

def snippet(txt: str, max_len: int = MAX_SNIPPET):
    return txt if len(txt) <= max_len else txt[:max_len-1] + "…"

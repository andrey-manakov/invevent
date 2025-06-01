"""In-memory create-event wizard."""
from datetime import datetime, timezone
from typing import Dict, Any, List

MAX_SNIPPET = 60
WIZ_STEPS = ["title", "description", "datetime", "location", "visibility", "confirm"]
WIZARDS: Dict[int, Dict[str, Any]] = {}

def snippet(text: str, max_len: int = MAX_SNIPPET) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"

def reset(user_id: int):
    WIZARDS.pop(user_id, None)

def start(user_id: int):
    reset(user_id)
    WIZARDS[user_id] = {"step": 0, "owner_id": user_id}

def get(user_id: int):
    return WIZARDS.get(user_id)

# wizard/wizard_utils.py

import uuid

# ─────────────────────────────────────────────────────────────────────────────
# A fixed list of “tags” used in step 3.  You can modify as needed.
TAGS = ["🎉 Party", "🎮 Gaming", "🍽️ Food", "🎬 Cinema"]
# ─────────────────────────────────────────────────────────────────────────────

def random_suffix():
    """
    Return a 4‐char random hex suffix, e.g. "1a2b".
    Used to generate default title/description if user taps “default.”
    """
    return uuid.uuid4().hex[:4]


def snippet(text: str, length: int = 200) -> str:
    """
    Trim `text` to at most `length` characters, appending an ellipsis if needed.
    (Used elsewhere if you want to preview descriptions, etc.)
    """
    if len(text) <= length:
        return text
    return text[:length] + "…"
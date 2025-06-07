# wizard/wizard_utils.py

import uuid

# ─────────────────────────────────────────────────────────────────────────────
# Topic list for the first wizard step (alphabetical order).
# These values are stored in the ``tags`` column of ``Event``.
TOPICS = [
    "business and work",
    "culture and education",
    "hangout and dine out",
    "health and beauty",
    "hobby and entertainment",
    "nature",
    "sport",
    "other",
]

# Mapping topic → list of event titles shown in step 1.
EVENT_OPTIONS = {
    "sport": ["run", "bike", "gym", "workout", "other"],
    "culture and education": [
        "theatre",
        "concert",
        "museum",
        "art",
        "lecture",
        "other",
    ],
    "hobby and entertainment": ["cinema", "master class", "other"],
    "hangout and dine out": ["lunch", "dinner", "drinks", "other"],
    "health and beauty": ["spa", "barber shop", "beauty salon", "other"],
    "business and work": ["office", "business trip", "conference", "other"],
    "nature": ["other"],
    "other": ["other"],
}
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
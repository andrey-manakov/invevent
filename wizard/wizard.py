# wizard/wizard.py

"""
Simple in-memory wizard state for each user.
Tracks which step (0..5) the user is on.
"""

STEPS = [
    "topic",
    "event",
    "datetime",
    "location",
    "picture",
    "description",
]

# { user_id: {"step": int, …other keys…} }
WIZ = {}

def start(uid):
    """
    Initialize a wizard session for user `uid`. 
    Puts them at step index 0.
    """
    WIZ[uid] = {"step": 0}

def get(uid):
    """
    Return the wizard‐state dict for user `uid`, or None if they’re not in a wizard.
    """
    return WIZ.get(uid)

def reset(uid):
    """
    Cancel and remove this user’s wizard‐state.
    """
    WIZ.pop(uid, None)

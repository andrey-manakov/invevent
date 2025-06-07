def cb(eid, act):
    return f"evt:{eid}:act:{act}"


def ucb(uid: int, act: str) -> str:
    """Return callback data for user-related actions."""
    return f"user:{uid}:act:{act}"

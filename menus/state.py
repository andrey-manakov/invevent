STATE = {}

def set_state(uid: int, val: str):
    STATE[uid] = val

def get_state(uid: int) -> str:
    return STATE.get(uid, "main")

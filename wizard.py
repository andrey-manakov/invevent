from datetime import datetime, timezone
from typing import Dict, Any

STEPS = ["title","description","datetime","tags","location","visibility","confirm"]
WIZ: Dict[int, Dict[str, Any]] = {}
MAX_LEN=200

def snippet(text:str,max_len:int=MAX_LEN):
    return text if len(text)<=max_len else text[:max_len-1]+"…"
def reset(uid:int): WIZ.pop(uid,None)
def start(uid:int): reset(uid); WIZ[uid]={"step":0}
def get(uid:int): return WIZ.get(uid)

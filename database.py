import json
import os
from config import EARLY_BIRD_LIMIT

DB_FILE = "db.json"

def _load():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "early_used": 0}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def _save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(user_id):
    db = _load()
    return db["users"].get(str(user_id))

def create_user(user_id):
    db = _load()
    uid = str(user_id)

    if uid in db["users"]:
        return db["users"][uid]

    early = db["early_used"] < EARLY_BIRD_LIMIT
    if early:
        db["early_used"] += 1

    db["users"][uid] = {
        "paid": False,
        "early": early,
        "timezone": "UTC",
        "threshold": 1.5,
        "exchanges": ["bybit"],
        "notify_before": 5
    }

    _save(db)
    return db["users"][uid]

def early_left():
    db = _load()
    return EARLY_BIRD_LIMIT - db["early_used"]

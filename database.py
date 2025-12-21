from datetime import datetime

USERS = {}
EARLY_BIRD_COUNT = 0

def init_db():
    global USERS
    USERS = {}

def get_user(user_id):
    return USERS.get(user_id)

def add_or_update_user(user_id, data):
    if user_id not in USERS:
        USERS[user_id] = {}
    USERS[user_id].update(data)

def get_plan(user_id):
    user = get_user(user_id)
    if not user:
        return "FREE"
    return user.get("plan", "FREE")

def increment_early_bird():
    global EARLY_BIRD_COUNT
    EARLY_BIRD_COUNT += 1

def get_early_bird_count():
    return EARLY_BIRD_COUNT

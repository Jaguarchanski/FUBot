users = {}  # chat_id -> {"threshold": float}

def add_user(chat_id: int, threshold: float = 1.5):
    users[chat_id] = {"threshold": threshold}

def update_threshold(chat_id: int, threshold: float):
    if chat_id in users:
        users[chat_id]["threshold"] = threshold

def get_users():
    return users

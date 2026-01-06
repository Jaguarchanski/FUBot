# Просте сховище користувачів у пам'яті
users = {}

def add_user(chat_id):
    if chat_id not in users:
        users[chat_id] = {"threshold": 1.5, "active": True}

def get_user(chat_id):
    return users.get(chat_id)

def get_active_users():
    return [uid for uid, u in users.items() if u["active"]]

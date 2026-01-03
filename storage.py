# Зберігає користувачів та їхні пороги funding
# Для простоти - зберігаємо у пам'яті (пізніше можна додати БД)

users = {}

def add_user(chat_id: int, plan: str = "free", funding_threshold: float = 1.5):
    users[chat_id] = {"plan": plan, "threshold": funding_threshold}

def update_threshold(chat_id: int, threshold: float):
    if chat_id in users:
        users[chat_id]["threshold"] = threshold

def get_users():
    return users

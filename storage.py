import asyncio

# Просте in-memory сховище для MVP
USERS = {}  # chat_id -> user_data
EARLY_BIRD_COUNTER = 0
lock = asyncio.Lock()

async def add_user(chat_id):
    global EARLY_BIRD_COUNTER
    async with lock:
        if chat_id not in USERS:
            plan = "free"
            early_bird = False
            if EARLY_BIRD_COUNTER < 500:
                early_bird = True
                EARLY_BIRD_COUNTER += 1
                plan = "early_bird"
            USERS[chat_id] = {
                "plan": plan,
                "early_bird": early_bird,
                "threshold": 1.5,
                "exchanges": ["bybit"],
                "notify_minutes": 5,
            }
            return USERS[chat_id]
        return USERS[chat_id]

def get_users():
    return USERS

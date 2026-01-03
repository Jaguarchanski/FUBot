from typing import Dict
from datetime import datetime

class User:
    def __init__(self, chat_id: int, plan: str = "free"):
        self.chat_id = chat_id
        self.plan = plan  # free або paid
        self.threshold = 1.5  # default для free
        self.exchanges = ["bybit"]  # default для free
        self.timezone_offset = 0
        self.alert_minutes = 5
        self.early_bird_start = datetime.now()

class Storage:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.early_bird_counter = 0

    def add_user(self, chat_id: int):
        if chat_id not in self.users:
            plan = "free"
            if self.early_bird_counter < 500:
                plan = "early_bird"
                self.early_bird_counter += 1
            self.users[chat_id] = User(chat_id, plan)
        return self.users[chat_id]

storage = Storage()

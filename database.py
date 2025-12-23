import json
import os

DB_FILE = "database.json"

def db_load():
    if not os.path.exists(DB_FILE):
        # Структура бази за замовчуванням
        return {"early_bird_remaining": 500, "users": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def db_save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

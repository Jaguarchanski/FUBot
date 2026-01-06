import os
from dotenv import load_dotenv

load_dotenv()

# Ми використовуємо назву TELEGRAM_TOKEN, щоб вона збігалася з main.py
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN") 

if not TELEGRAM_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

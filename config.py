import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env (для локальної розробки)
load_dotenv()

class Config:
    def __init__(self):
        # Ми беремо значення з BOT_TOKEN (як у тебе в Render), 
        # але всередині програми називаємо його TELEGRAM_TOKEN для зручності
        self.TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
        
        # Інші змінні
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        self.PROXY_URL = os.getenv("PROXY_URL")
        
        # Перевірка для логів (щоб ти бачив, чи завантажився токен)
        if not self.TELEGRAM_TOKEN:
            print("⚠️ ПОПЕРЕДЖЕННЯ: BOT_TOKEN не знайдено в змінних оточення!")

# Створюємо екземпляр класу для використання в інших файлах
config = Config()

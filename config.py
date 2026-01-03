import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL для FastAPI webhook
PROXY_URL = os.getenv("PROXY_URL", None)  # якщо потрібно
EARLY_BIRD_LIMIT = 500
FREE_PLAN_THRESHOLD = 1.5  # Максимальний funding для безкоштовного плану
FUNDING_INTERVAL = 60  # перевірка funding у секундах

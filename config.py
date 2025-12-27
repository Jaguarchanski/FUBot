import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://yourdomain.com/webhook
PORT = int(os.getenv("PORT", 8000))

EARLY_BIRD_LIMIT = 500
FREE_THRESHOLD = 1.5  # % funding для безкоштовного плану

# Список бірж
EXCHANGES = ["bybit", "binance", "okx", "ftx", "kucoin", "bitget", "gateio", "huobi", "mexc"]

# config.py — Безпечна версія (токен і гаманець беруться з змінних Render)
import os

# Токен бота — береться з змінної середовища Render (обов'язково додай її там)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# USDT-гаманець для виводу з Crypto Pay (додай як змінну на Render, якщо хочеш)
USDT_WALLET = os.getenv("USDT_WALLET", "")

# Твій admin ID (можеш залишити в коді або теж в змінну)
ADMIN_ID = 123456789  # заміни на свій user_id з @userinfobot

# Налаштування бота
EARLY_BIRD_LIMIT = 500      # кількість безкоштовних PRO на старті
PRO_PRICE_USDT = 50         # ціна PRO в USDT
PRO_DAYS = 30               # кількість днів PRO

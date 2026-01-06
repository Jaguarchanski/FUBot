import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import config
from database.db import init_db
from funding.fetcher import fetch_all_funding_rates
from telegram_bot.bot import start_command, threshold_command, list_command

# Налаштування логів
logging.basicConfig(level=logging.INFO)

# Створюємо додаток
application = Application.builder().token(config.TELEGRAM_TOKEN).build()

# Реєструємо команди
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("threshold", threshold_command))
application.add_handler(CommandHandler("list", list_command))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ВАЖЛИВО: Ініціалізація бота перед запуском
    await application.initialize()
    await application.start()
    
    # Встановлення вебхука
    webhook_url = f"{config.WEBHOOK_URL.rstrip('/')}/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logging.info(f"✅ Webhook встановлено: {webhook_url}")
    
    # Ініціалізація БД
    await init_db()
    
    # Запуск фонового циклу
    import asyncio
    asyncio.create_task(background_monitor())
    
    yield
    
    # Закриття при зупинці
    await application.stop()
    await application.shutdown()

async def background_monitor():
    logging.info("Початок перевірки бірж...")
    while True:
        try:
            rates = await fetch_all_funding_rates()
            # Тут можна додати логіку порівняння з порогом, як у твоїй версії
            logging.info(f"Отримано {len(rates)} ставок")
        except Exception as e:
            logging.error(f"Помилка моніторингу: {e}")
        await asyncio.sleep(600)

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def index():
    return {"status": "bot is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

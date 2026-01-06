import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler

# Виправляємо шлях, щоб Python бачив папки як модулі
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from database.db import init_db
from telegram_bot.bot import start_command, threshold_command, list_command

logging.basicConfig(level=logging.INFO)

# Ініціалізація Telegram Application
application = Application.builder().token(config.TELEGRAM_TOKEN).build()

# Реєстрація команд
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("threshold", threshold_command))
application.add_handler(CommandHandler("list", list_command))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Запуск бота
    await application.initialize()
    await application.start()
    
    # 2. Налаштування вебхука
    webhook_url = f"{config.WEBHOOK_URL.rstrip('/')}/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logging.info(f"🚀 FURate запущено: {webhook_url}")
    
    # 3. База даних
    await init_db()
    
    yield
    
    # Зупинка при вимкненні сервера
    await application.stop()
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def index():
    return {"status": "FURate is Online"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

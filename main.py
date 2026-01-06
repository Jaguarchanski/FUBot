import logging
import uvicorn
import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from contextlib import asynccontextmanager

from config import TELEGRAM_TOKEN
from telegram_bot.bot import start_command, button_handler
from database.db import init_db

# Налаштування логів
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Створюємо об'єкт додатку Telegram
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ініціалізація бази даних
    await init_db()
    
    # Реєстрація обробників
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CallbackQueryHandler(button_handler))
    
    # Запуск Telegram додатку
    await tg_app.initialize()
    await tg_app.start()
    logger.info("🚀 Telegram Bot started successfully")
    
    yield
    
    # Зупинка
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return {"status": "error"}

@app.get("/")
async def index():
    return {"status": "Bot is running", "promo": "500 slots campaign active"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

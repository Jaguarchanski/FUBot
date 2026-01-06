import logging
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from contextlib import asynccontextmanager

from config import TELEGRAM_TOKEN
from telegram_bot.bot import start_command, button_handler
from database.db import init_db

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Створюємо об'єкт додатку Telegram
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Новий спосіб ініціалізації замість on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Дії при старті
    await init_db()
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CallbackQueryHandler(button_handler))
    
    await tg_app.initialize()
    await tg_app.start()
    logger.info("Telegram Bot started successfully")
    
    yield
    
    # Дії при зупинці
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def index():
    return {"status": "Bot is running"}

if __name__ == "__main__":
    # Render передає порт через змінну оточення
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

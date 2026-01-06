import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_TOKEN
from telegram_bot.bot import start_command, button_handler
from database.db import init_db

# Налаштування логів
logging.basicConfig(level=logging.INFO)

app = FastAPI()
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

@app.on_event("startup")
async def startup():
    await init_db() # Ініціалізація бази при старті
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CallbackQueryHandler(button_handler)) # Обробник кнопок
    await tg_app.initialize()
    await tg_app.start()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"status": "ok"}

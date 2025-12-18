# main.py
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
import logging
import os

# =============================
# Налаштування логів
# =============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =============================
# Ініціалізація FastAPI
# =============================
app = FastAPI()

# =============================
# Токен бота
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Рекомендую ставити токен в змінні середовища
if not BOT_TOKEN:
    raise ValueError("Встанови BOT_TOKEN у змінні середовища")

# =============================
# Ініціалізація асинхронного Application
# =============================
application = ApplicationBuilder().token(BOT_TOKEN).build()

# =============================
# Обробники команд і повідомлень
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Бот запущено!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ти написав: {update.message.text}")

# Додаємо хендлери
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# =============================
# Вебхук FastAPI
# =============================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"Помилка при обробці вебхука: {e}")
    return {"ok": True}

# =============================
# Запуск бота через Render
# =============================
async def start_bot():
    await application.initialize()
    await application.start()
    # Тут можна додати polling, але для вебхука він не потрібен
    logging.info("Бот успішно стартував!")

# =============================
# Точка входу для uvicorn
# =============================
if __name__ == "__main__":
    import uvicorn
    asyncio.run(start_bot())  # Ініціалізуємо бот перед запуском FastAPI
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

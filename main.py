# main.py
import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ------------------------------
# Логування
# ------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Встанови BOT_TOKEN у змінні середовища")

# ------------------------------
# FastAPI
# ------------------------------
app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ------------------------------
# Функції обробки команд
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Опція 1", callback_data="option_1")],
        [InlineKeyboardButton("Опція 2", callback_data="option_2")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привіт! Обери опцію:", reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Це приклад бота з кнопками та вебхуком.")

# ------------------------------
# Callback для кнопок
# ------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # обов'язково відповісти
    if query.data == "option_1":
        await query.edit_message_text(text="Ти обрав Опцію 1")
    elif query.data == "option_2":
        await query.edit_message_text(text="Ти обрав Опцію 2")

# ------------------------------
# Обробка тексту користувача
# ------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "привіт" in text:
        await update.message.reply_text("Привіт! Раді тебе бачити 🙂")
    else:
        await update.message.reply_text(f"Ти написав: {update.message.text}")

# ------------------------------
# Реєстрація хендлерів
# ------------------------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

# ------------------------------
# Вебхук для FastAPI
# ------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# ------------------------------
# Події старту та завершення FastAPI
# ------------------------------
@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
    logging.info("Бот успішно стартував!")

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()
    logging.info("Бот завершив роботу")

# ------------------------------
# Локальний запуск (uvicorn)
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

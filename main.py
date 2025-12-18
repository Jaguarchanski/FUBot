import logging
import os
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# -------------------
# Налаштування логів
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -------------------
# Змінні середовища Render
TOKEN = os.environ.get("BOT_TOKEN")
URL = os.environ.get("RENDER_EXTERNAL_URL")  # наприклад: https://fubot.onrender.com

# -------------------
bot = Bot(TOKEN)
app = ApplicationBuilder().token(TOKEN).build()

# -------------------
# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [("Натисни мене", "button_click")]
    ]
    await update.message.reply_text(
        "Привіт! Це тест кнопки.",
        reply_markup=telegram.InlineKeyboardMarkup.from_button_data(keyboard)
    )

# -------------------
# Callback кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Ти натиснув кнопку!")

# -------------------
# Додаємо хендлери
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

# -------------------
# Aiohttp сервер для вебхука
async def handle(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await app.process_update(update)
    return web.Response(text="OK")

web_app = web.Application()
web_app.router.add_post("/webhook", handle)

# -------------------
# Запуск webhook на Render
async def main():
    await bot.delete_webhook()  # на всякий випадок очистити старий вебхук
    await bot.set_webhook(f"{URL}/webhook")
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8000)))
    await site.start()
    print("Бот запущено!")

import asyncio
asyncio.run(main())

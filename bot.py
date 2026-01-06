import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from storage import add_user, get_user

BOT_TOKEN = os.getenv("BOT_TOKEN")
application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await update.message.reply_text("✅ Ви підписані на funding alert!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Команди: /start, /help, /threshold")

async def threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if context.args:
        try:
            value = float(context.args[0])
            user = get_user(chat_id)
            if user:
                user["threshold"] = value
                await update.message.reply_text(f"✅ Поріг встановлено: {value}%")
        except:
            await update.message.reply_text("❌ Некоректне значення")
    else:
        await update.message.reply_text("ℹ️ Використання: /threshold <значення>")

def setup_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("threshold", threshold))
    application.run_polling()  # Локальний тест, на Render webhook потрібно міняти

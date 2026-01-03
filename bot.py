from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from storage import add_user, update_threshold

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await update.message.reply_text(
        "Вітаю! Ти підписаний на funding alerts. Використай /set_threshold щоб змінити поріг."
    )

async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        value = float(context.args[0])
        update_threshold(chat_id, value)
        await update.message.reply_text(f"Поріг оновлено до {value}%")
    except:
        await update.message.reply_text("Використання: /set_threshold <значення>")

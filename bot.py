from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from storage import storage

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = storage.add_user(update.effective_chat.id)
    await update.message.reply_text(
        f"Привіт! Ти отримав {user.plan} план.\n"
        f"Залишилось місць для early-bird: {500 - storage.early_bird_counter}"
    )

async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(context.args[0])
        user = storage.users[update.effective_chat.id]
        user.threshold = value
        await update.message.reply_text(f"Мінімальний поріг встановлено на {value}%")
    except:
        await update.message.reply_text("Введіть число після /set_threshold")

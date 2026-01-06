from telegram import Update
from telegram.ext import ContextTypes
import logging

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Вітаю у FURate! Я твій помічник для моніторингу ставок фандингу.\n\n"
        "Команди:\n"
        "📈 /list — Показати актуальні високі ставки\n"
        "🎯 /threshold [число] — Встановити поріг сповіщень (напр. 0.01)\n"
        "ℹ️ /help — Допомога"
    )

async def threshold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Вкажіть поріг. Наприклад: `/threshold 0.01`")
        return
    try:
        new_threshold = float(context.args[0])
        # Збереження в БД додамо в наступному кроці
        await update.message.reply_text(f"✅ Для FURate встановлено новий поріг: {new_threshold}%")
    except ValueError:
        await update.message.reply_text("❌ Помилка: введіть число через крапку (напр. 0.02)")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 FURate збирає дані з бірж... Зачекайте хвилину.")

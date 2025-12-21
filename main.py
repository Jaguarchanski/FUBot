import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from funding_sources_all import get_all_funding, format_funding_message

TOKEN = os.getenv("BOT_TOKEN")

user_lang = {}

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(
        "Оберіть мову / Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- LANGUAGE ----------
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    user_lang[query.from_user.id] = lang

    keyboard = [
        [InlineKeyboardButton("📊 Топ фандинг", callback_data="top_funding")]
    ]

    await query.edit_message_text(
        "Мову встановлено ✅",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- TOP FUNDING ----------
async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    results = await get_all_funding()
    lang = user_lang.get(query.from_user.id, "ua")

    text = format_funding_message(results, lang)
    await query.edit_message_text(text)

# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(top_funding, pattern="^top_funding$"))

    app.run_polling()

if __name__ == "__main__":
    main()

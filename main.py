import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
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

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

WEBHOOK_PATH = "/webhook"
WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH

# ================== BOT ==================
application = Application.builder().token(BOT_TOKEN).build()

# ================== HANDLERS ==================
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

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_ua":
        text = "✅ Мову встановлено: Українська\n\nВиберіть дію:"
        keyboard = [
            [InlineKeyboardButton("ℹ️ Про бота", callback_data="about")],
            [InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")],
        ]
    else:
        text = "✅ Language set: English\n\nChoose action:"
        keyboard = [
            [InlineKeyboardButton("ℹ️ About bot", callback_data="about")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🤖 Це Telegram-бот.\n\nФункціонал буде розширюватись."
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "⚙️ Налаштування наразі недоступні."
    )

# ================== REGISTRATION ==================
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
application.add_handler(CallbackQueryHandler(about, pattern="^about$"))
application.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))

# ================== FASTAPI ==================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_FULL_URL)
    print(f"Webhook встановлено: {WEBHOOK_FULL_URL}")
    yield
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}

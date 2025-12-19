import os
import logging
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

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"
WEBHOOK_FULL_URL = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

# ---------------- BOT ----------------

application = Application.builder().token(BOT_TOKEN).build()

# ---------------- HANDLERS ----------------

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
        text = "✅ Мову встановлено: Українська\n\nНатисніть кнопку нижче 👇"
        keyboard = [
            [InlineKeyboardButton("📊 Функціонал", callback_data="features")]
        ]
    else:
        text = "✅ Language set: English\n\nPress the button below 👇"
        keyboard = [
            [InlineKeyboardButton("📊 Features", callback_data="features")]
        ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🚀 Бот працює коректно.\n\n"
        "✔ Webhook\n"
        "✔ FastAPI\n"
        "✔ Inline кнопки\n"
        "✔ Готовий до масштабування (1000+ юзерів)",
    )

# ---------------- REGISTER ----------------

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
application.add_handler(CallbackQueryHandler(features, pattern="^features$"))

# ---------------- FASTAPI ----------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_FULL_URL)
    await application.start()
    logger.info(f"Webhook встановлено: {WEBHOOK_FULL_URL}")
    yield
    await application.stop()

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

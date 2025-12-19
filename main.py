import os
import asyncio
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

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://fubot.onrender.com/webhook

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

# =========================
# BOT APP
# =========================
bot_app = Application.builder().token(BOT_TOKEN).build()

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    await update.message.reply_text(
        "Оберіть мову / Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_ua":
        text = (
            "✅ Мову встановлено: Українська\n\n"
            "📌 Доступні команди:\n"
            "/start — перезапуск\n"
            "/help — допомога"
        )
    else:
        text = (
            "✅ Language set: English\n\n"
            "📌 Available commands:\n"
            "/start — restart\n"
            "/help — help"
        )

    await query.edit_message_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Це тестовий бот.\nФункціонал буде розширюватися."
    )

# =========================
# REGISTER HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CallbackQueryHandler(language_handler))

# =========================
# FASTAPI
# =========================
api = FastAPI()

@api.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL}")

@api.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@api.get("/")
async def health():
    return {"status": "ok"}

# =========================
# RUN
# =========================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:api",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
    )

import os
import logging
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

# ================== НАЛАШТУВАННЯ ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://fubot.onrender.com

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

logging.basicConfig(level=logging.INFO)

# ================== FASTAPI ==================

app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ================== КНОПКИ ==================

def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]
        ]
    )


def main_menu(lang: str):
    if lang == "ua":
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📊 Старт аналізу", callback_data="start_scan")],
                [InlineKeyboardButton("ℹ️ Про бота", callback_data="about")],
            ]
        )
    else:
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📊 Start scan", callback_data="start_scan")],
                [InlineKeyboardButton("ℹ️ About bot", callback_data="about")],
            ]
        )


# ================== ХЕНДЛЕРИ ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оберіть мову / Choose language:",
        reply_markup=language_keyboard(),
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "lang_ua":
        context.user_data["lang"] = "ua"
        await query.edit_message_text(
            "✅ Мову встановлено",
            reply_markup=main_menu("ua"),
        )

    elif data == "lang_en":
        context.user_data["lang"] = "en"
        await query.edit_message_text(
            "✅ Language selected",
            reply_markup=main_menu("en"),
        )

    elif data == "start_scan":
        lang = context.user_data.get("lang", "ua")
        text = (
            "🔍 Сканування обʼємів запущено (демо)"
            if lang == "ua"
            else "🔍 Volume scan started (demo)"
        )
        await query.edit_message_text(text)

    elif data == "about":
        lang = context.user_data.get("lang", "ua")
        text = (
            "🤖 Бот для пошуку аномального обʼєму на низьколіквідних монетах"
            if lang == "ua"
            else "🤖 Bot for detecting abnormal volume on low-liquidity coins"
        )
        await query.edit_message_text(text)


# ================== TELEGRAM APP ==================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(callbacks))


# ================== WEBHOOK ==================

@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logging.info("Webhook встановлено")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/")
async def healthcheck():
    return {"status": "ok"}

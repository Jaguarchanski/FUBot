import os
import logging
from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================== НАЛАШТУВАННЯ ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://fubot.onrender.com/webhook
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Зберігання станів користувачів
USER_LANG = {}

# ================== КНОПКИ ==================
def language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])

def main_menu(lang: str):
    if lang == "ua":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Функціонал", callback_data="menu_features")],
            [InlineKeyboardButton("ℹ️ Про бота", callback_data="menu_about")],
            [InlineKeyboardButton("⚙️ Налаштування", callback_data="menu_settings")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Features", callback_data="menu_features")],
            [InlineKeyboardButton("ℹ️ About", callback_data="menu_about")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")]
        ])

def back_button(lang):
    text = "⬅️ Назад" if lang == "ua" else "⬅️ Back"
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data="menu_back")]])

# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оберіть мову / Choose your language:",
        reply_markup=language_keyboard()
    )

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    USER_LANG[query.from_user.id] = lang

    text = (
        "✅ Мову встановлено.\nОберіть пункт меню:"
        if lang == "ua"
        else "✅ Language set.\nChoose menu item:"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=main_menu(lang)
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang = USER_LANG.get(user_id, "ua")

    if query.data == "menu_features":
        text = (
            "📊 Тут буде основний функціонал бота."
            if lang == "ua"
            else "📊 Main bot functionality will be here."
        )
        await query.edit_message_text(text, reply_markup=back_button(lang))

    elif query.data == "menu_about":
        text = (
            "ℹ️ Цей бот створений для подальшого розширення функціоналу."
            if lang == "ua"
            else "ℹ️ This bot is designed for further feature expansion."
        )
        await query.edit_message_text(text, reply_markup=back_button(lang))

    elif query.data == "menu_settings":
        text = (
            "⚙️ Налаштування будуть доступні згодом."
            if lang == "ua"
            else "⚙️ Settings will be available later."
        )
        await query.edit_message_text(text, reply_markup=back_button(lang))

    elif query.data == "menu_back":
        text = (
            "Головне меню:"
            if lang == "ua"
            else "Main menu:"
        )
        await query.edit_message_text(text, reply_markup=main_menu(lang))

# ================== APPLICATION ==================
application = ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(language_handler, pattern="^lang_"))
application.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu_"))

# ================== WEBHOOK ==================
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook встановлено: {WEBHOOK_URL}")

# ================== ROOT ==================
@app.get("/")
async def root():
    return {"status": "Bot is running"}

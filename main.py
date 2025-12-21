import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources_all import get_all_funding, format_funding_message

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

bot_app = Application.builder().token(BOT_TOKEN).build()
init_db()
FREE_THRESHOLD = 1.5

# =========================
# Helpers
# =========================
def main_menu(lang, plan):
    keyboard = [
        [InlineKeyboardButton("Фільтри", callback_data='filter_main')],
        [InlineKeyboardButton("Топ фандінг", callback_data='top_funding')],
        [InlineKeyboardButton("Акаунт", callback_data='account')],
    ]
    if plan == 'FREE':
        keyboard.append([InlineKeyboardButton("Отримати PRO", callback_data='get_pro')])
    return InlineKeyboardMarkup(keyboard)

async def safe_edit_message(query, text, reply_markup=None):
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception:
        await query.message.reply_text(text, reply_markup=reply_markup)

# =========================
# Команди
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        keyboard = [
            [InlineKeyboardButton("🇺🇦 Українська", callback_data='lang_uk')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        ]
        await update.message.reply_text("Вітаю! Оберіть мову / Choose language:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    lang = user.get('language', 'uk')
    plan = get_plan(user_id)

    # Early bird
    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        await update.message.reply_text(f"Ви отримали PRO! ({get_early_bird_count()})", reply_markup=main_menu(lang, "PRO"))
        return

    await update.message.reply_text("Ласкаво просимо!", reply_markup=main_menu(lang, plan))

async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user.get("language", "uk")
    plan = get_plan(query.from_user.id)
    funding_list = get_all_funding()
    message = format_funding_message(funding_list, plan, lang)
    await safe_edit_message(query, message, reply_markup=main_menu(lang, plan))

# =========================
# Callback меню
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))

# =========================
# FastAPI
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:api", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

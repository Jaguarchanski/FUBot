import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources_all import get_all_funding, format_funding_message
from i18n import get_text
from config import BOT_TOKEN

# =========================
# ENV
# =========================
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

# =========================
# BOT APP
# =========================
bot_app = Application.builder().token(BOT_TOKEN).build()

init_db()
FREE_THRESHOLD = 1.5

# =========================
# HELPERS
# =========================
def main_menu(lang, plan):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'filter_button'), callback_data='filter_main')],
        [InlineKeyboardButton(get_text(lang, 'top_funding_button'), callback_data='top_funding')],
        [InlineKeyboardButton(get_text(lang, 'account_button'), callback_data='account')],
    ]
    if plan == 'FREE':
        keyboard.append([InlineKeyboardButton(get_text(lang, 'get_pro_button'), callback_data='get_pro')])
    return InlineKeyboardMarkup(keyboard)

async def safe_edit_message(query, text, reply_markup=None):
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception:
        await query.message.reply_text(text, reply_markup=reply_markup)

# =========================
# COMMAND HANDLERS
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

    lang = user['language']
    plan = get_plan(user_id)

    # Early bird
    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        await update.message.reply_text(get_text(lang, 'early_bird').format(num=count), reply_markup=main_menu(lang, "PRO"))
        return

    await update.message.reply_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = 'uk' if query.data == 'lang_uk' else 'en'
    add_or_update_user(query.from_user.id, {"language": lang})
    plan = get_plan(query.from_user.id)
    await safe_edit_message(query, get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

# =========================
# CALLBACK HANDLERS
# =========================
async def go_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']
    plan = get_plan(query.from_user.id)
    await safe_edit_message(query, get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    expires = user.get('plan_expires')
    expires_str = expires.strftime("%d.%m.%Y") if expires else "FREE"
    text = (
        f"Тариф: {plan}\n"
        f"Інтервал: {user.get('interval', '-') } хв\n"
        f"Поріг: {user.get('threshold', '-')}%\n"
        f"Біржа: {', '.join(user.get('exchanges', [])) or '-'}\n"
        f"PRO до: {expires_str}\n"
        f"Часовий пояс: UTC{user.get('timezone', 0)}"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

async def get_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if get_plan(user_id) == "PRO":
        await safe_edit_message(query, "У вас вже є PRO!")
        return
    invoice_link = f"https://t.me/CryptoBot?start=pay_50usdt_{user_id}_pro"
    keyboard = [[InlineKeyboardButton("Оплатити 50 USDT", url=invoice_link)]]
    await safe_edit_message(query, "PRO-тариф — 50 USDT/міс\nОплата через @CryptoBot", reply_markup=InlineKeyboardMarkup(keyboard))

async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']
    plan = get_plan(query.from_user.id)

    # =========================
    # Виклик функції з нового файлу
    # =========================
    funding_list = get_all_funding()
    message = format_funding_message(funding_list, plan, lang)
    await safe_edit_message(query, get_text(lang, 'auto_message') + "\n" + message, reply_markup=main_menu(lang, plan))

# =========================
# FILTER MENU AND SUBMENUS
# =========================
async def filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']

    keyboard = [
        [InlineKeyboardButton(get_text(lang, "set_timezone"), callback_data="set_timezone")],
        [InlineKeyboardButton(get_text(lang, "select_exchanges"), callback_data="select_exchanges")],
        [InlineKeyboardButton(get_text(lang, "set_threshold"), callback_data="set_threshold")],
        [InlineKeyboardButton("⬅️ " + get_text(lang, "main_menu"), callback_data="main_menu")]
    ]
    await safe_edit_message(query, get_text(lang, "filter_menu"), reply_markup=InlineKeyboardMarkup(keyboard))

# =========================
# REGISTER HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(language_handler, pattern='^lang_'))
bot_app.add_handler(CallbackQueryHandler(go_main_menu, pattern='^main_menu$'))
bot_app.add_handler(CallbackQueryHandler(account, pattern='^account$'))
bot_app.add_handler(CallbackQueryHandler(get_pro, pattern='^get_pro$'))
bot_app.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))
bot_app.add_handler(CallbackQueryHandler(filter_menu, pattern='^filter_main$'))

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

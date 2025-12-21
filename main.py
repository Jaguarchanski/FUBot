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
from funding_sources_all import *  # <-- новий об'єднаний файл з усіма біржами
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
    funding_list = get_all_funding()  # <-- використання нової об'єднаної функції
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
# TIMEZONE HANDLER
# =========================
async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']

    keyboard = [[InlineKeyboardButton(f"UTC{tz}", callback_data=f"timezone_{tz}") for tz in range(-12, 15)]]
    keyboard.append([InlineKeyboardButton("⬅️ " + get_text(lang, "main_menu"), callback_data="main_menu")])
    await safe_edit_message(query, get_text(lang, "choose_timezone"), reply_markup=InlineKeyboardMarkup(keyboard))

async def timezone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tz = int(query.data.split("_")[1])
    add_or_update_user(query.from_user.id, {"timezone": tz})
    await safe_edit_message(query, f"Timezone set to UTC{tz}", reply_markup=main_menu(get_user(query.from_user.id)["language"], get_plan(query.from_user.id)))

# =========================
# EXCHANGES HANDLER
# =========================
async def select_exchanges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']

    exchanges = ["Bybit", "Binance", "Bitget", "MEXC", "OKX", "KuCoin", "HTX", "Gate.io", "BingX"]
    keyboard = [[InlineKeyboardButton(e, callback_data=f"exchange_{e}") for e in exchanges[i:i+3]] for i in range(0, len(exchanges), 3)]
    keyboard.append([InlineKeyboardButton("⬅️ " + get_text(lang, "main_menu"), callback_data="main_menu")])
    await safe_edit_message(query, get_text(lang, "choose_exchanges"), reply_markup=InlineKeyboardMarkup(keyboard))

async def exchange_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exchange = query.data.split("_")[1]
    user = get_user(query.from_user.id)
    exchanges = user.get("exchanges", [])
    if exchange not in exchanges:
        exchanges.append(exchange)
    add_or_update_user(query.from_user.id, {"exchanges": exchanges})
    await safe_edit_message(query, f"Selected exchanges: {', '.join(exchanges)}", reply_markup=main_menu(user["language"], get_plan(query.from_user.id)))

# =========================
# THRESHOLD HANDLER
# =========================
async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']

    keyboard = [
        [InlineKeyboardButton("0.5%", callback_data="threshold_0.5"),
         InlineKeyboardButton("1%", callback_data="threshold_1"),
         InlineKeyboardButton("1.5%", callback_data="threshold_1.5")],
        [InlineKeyboardButton("⬅️ " + get_text(lang, "main_menu"), callback_data="main_menu")]
    ]
    await safe_edit_message(query, get_text(lang, "set_threshold_text"), reply_markup=InlineKeyboardMarkup(keyboard))

async def threshold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    threshold = float(query.data.split("_")[1])
    add_or_update_user(query.from_user.id, {"threshold": threshold})
    await safe_edit_message(query, f"Threshold set to {threshold}%", reply_markup=main_menu(get_user(query.from_user.id)["language"], get_plan(query.from_user.id)))

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

bot_app.add_handler(CallbackQueryHandler(set_timezone, pattern="^set_timezone$"))
bot_app.add_handler(CallbackQueryHandler(timezone_handler, pattern="^timezone_"))
bot_app.add_handler(CallbackQueryHandler(select_exchanges, pattern="^select_exchanges$"))
bot_app.add_handler(CallbackQueryHandler(exchange_handler, pattern="^exchange_"))
bot_app.add_handler(CallbackQueryHandler(set_threshold, pattern="^set_threshold$"))
bot_app.add_handler(CallbackQueryHandler(threshold_handler, pattern="^threshold_"))

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

# main.py — FastAPI + python-telegram-bot v21 (Render-ready)

import os
import asyncio
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from database import (
    init_db,
    get_user,
    add_or_update_user,
    get_plan,
    increment_early_bird,
    get_early_bird_count
)
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text
from config import BOT_TOKEN

# ===================== CONFIG =====================

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://fubot.onrender.com" + WEBHOOK_PATH)
PORT = int(os.getenv("PORT", 10000))
FREE_THRESHOLD = 1.5

# ===================== APP =====================

api = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

init_db()

# ===================== UI =====================

def main_menu(lang: str, plan: str):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'filter_button'), callback_data='filter_main')],
        [InlineKeyboardButton(get_text(lang, 'top_funding_button'), callback_data='top_funding')],
        [InlineKeyboardButton(get_text(lang, 'account_button'), callback_data='account')],
    ]
    if plan == "FREE":
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, 'get_pro_button'), callback_data='get_pro')]
        )
    return InlineKeyboardMarkup(keyboard)

# ===================== HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        keyboard = [
            [InlineKeyboardButton("Українська", callback_data="lang_uk")],
            [InlineKeyboardButton("English", callback_data="lang_en")],
        ]
        await update.message.reply_text(
            "Вітаю! Оберіть мову:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    lang = user["language"]
    plan = get_plan(user_id)

    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {
            "plan": "PRO",
            "plan_expires": expires
        })
        increment_early_bird()
        count = get_early_bird_count()

        await update.message.reply_text(
            get_text(lang, "early_bird").format(num=count),
            reply_markup=main_menu(lang, "PRO")
        )
    else:
        await update.message.reply_text(
            get_text(lang, "start_message"),
            reply_markup=main_menu(lang, plan)
        )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = "uk" if query.data == "lang_uk" else "en"
    user_id = query.from_user.id

    add_or_update_user(user_id, {
        "language": lang,
        "plan": "FREE",
        "interval": 60,
        "threshold": 1.0,
        "exchange": "ALL"
    })

    await query.edit_message_text(
        get_text(lang, "start_message"),
        reply_markup=main_menu(lang, "FREE")
    )

async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    lang = user["language"]
    plan = get_plan(query.from_user.id)

    funding = get_all_funding()
    message = format_funding_message(funding, plan, lang)

    await query.edit_message_text(
        get_text(lang, "auto_message") + "\n" + message,
        reply_markup=main_menu(lang, plan)
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    lang = user["language"]
    plan = get_plan(query.from_user.id)

    expires = user["plan_expires"]
    expires_str = expires.strftime("%d.%m.%Y") if expires else "FREE"

    text = (
        f"Тариф: {plan}\n"
        f"Інтервал: {user['interval']} хв\n"
        f"Поріг: {user['threshold']}%\n"
        f"Біржа: {user['exchange']}\n"
        f"PRO до: {expires_str}"
    )

    await query.edit_message_text(text, reply_markup=main_menu(lang, plan))

async def get_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if get_plan(user_id) == "PRO":
        await query.edit_message_text("У вас вже є PRO!")
        return

    invoice = f"https://t.me/CryptoBot?start=pay_50usdt_{user_id}_pro"
    keyboard = [[InlineKeyboardButton("Оплатити 50 USDT", url=invoice)]]

    await query.edit_message_text(
        "PRO — 50 USDT / місяць\nОплата через @CryptoBot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===================== FUNDING =====================

def get_all_funding():
    functions = [
        get_funding_bybit, get_funding_binance, get_funding_bitget,
        get_funding_mexc, get_funding_okx, get_funding_kucoin,
        get_funding_htx, get_funding_gateio, get_funding_bingx
    ]
    data = []
    for f in functions:
        try:
            data.extend(f())
        except Exception as e:
            print(f"{f.__name__} error:", e)
    return data

def format_funding_message(funding, plan, lang):
    funding.sort(key=lambda x: x["funding_rate"], reverse=True)
    lines = []

    for f in funding[:10]:
        rate = f["funding_rate"]
        time_str = f["next_funding_time"].strftime("%H:%M")
        if plan == "FREE" and rate > FREE_THRESHOLD:
            lines.append(f"{rate:.2f}% о {time_str} на {f['exchange']}")
        else:
            lines.append(f"{rate:.2f}% о {time_str} → {f['symbol']} ({f['exchange']})")

    return "\n".join(lines) if lines else get_text(lang, "no_funding")

# ===================== ROUTES =====================

@api.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@api.get("/")
def healthcheck():
    return {"status": "ok"}

# ===================== STARTUP =====================

@api.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL}")

# ===================== HANDLER REG =====================

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
application.add_handler(CallbackQueryHandler(top_funding, pattern="^top_funding$"))
application.add_handler(CallbackQueryHandler(account, pattern="^account$"))
application.add_handler(CallbackQueryHandler(get_pro, pattern="^get_pro$"))

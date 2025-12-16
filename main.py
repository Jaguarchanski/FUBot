# main.py — Версія 4.0 (v20, асинхронна, не висне, повне меню + фільтр + кнопка Назад)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text
from config import BOT_TOKEN, USDT_WALLET, ADMIN_ID, EARLY_BIRD_LIMIT, PRO_PRICE_USDT, PRO_DAYS
from datetime import datetime, timedelta
import pytz
import threading

logging.basicConfig(level=logging.INFO)

FREE_THRESHOLD = 1.5
ALL_EXCHANGES = ['Bybit', 'Binance', 'Bitget', 'MEXC', 'OKX', 'KuCoin', 'HTX', 'Gate.io', 'BingX']
TIMEZONES = ['UTC', 'Europe/Kiev', 'Europe/London', 'America/New_York', 'America/Chicago', 'Asia/Dubai', 'Asia/Singapore', 'Asia/Hong_Kong']

init_db()

def main_menu(lang, plan):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'filter_button'), callback_data='filter_main')],
        [InlineKeyboardButton(get_text(lang, 'top_funding_button'), callback_data='top_funding')],
        [InlineKeyboardButton(get_text(lang, 'account_button'), callback_data='account')],
    ]
    if plan == 'FREE':
        keyboard.append([InlineKeyboardButton(get_text(lang, 'get_pro_button'), callback_data='get_pro')])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        keyboard = [
            [InlineKeyboardButton("Українська", callback_data='lang_uk')],
            [InlineKeyboardButton("English", callback_data='lang_en')],
        ]
        await update.message.reply_text("Вітаю! Оберіть мову:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    lang = user['language']
    plan = get_plan(user_id)

    if plan == "FREE" and get_early_bird_count() < EARLY_BIRD_LIMIT:
        expires = datetime.now() + timedelta(days=PRO_DAYS)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        await update.message.reply_text(get_text(lang, 'early_bird').format(num=count), reply_markup=main_menu(lang, "PRO"))
    else:
        await update.message.reply_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

    context.job_queue.run_repeating(send_periodic_funding, interval=user['interval'] * 60, first=10, data=user_id, name=str(user_id))

async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    user_id = query.from_user.id
    data = {"language": lang, "plan": "FREE", "interval": 5, "threshold": 1.5, "exchange": "Bybit", "timezone": "UTC"}
    add_or_update_user(user_id, data)
    await query.edit_message_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, "FREE"))

async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    funding_list = get_all_funding()
    message = format_funding_message(funding_list, plan, lang)
    await query.edit_message_text(get_text(lang, 'auto_message') + "\n" + message, reply_markup=main_menu(lang, plan))

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    expires = user['plan_expires']
    expires_str = expires.strftime("%d.%m.%Y") if expires else "FREE"
    text = f"Тариф: {plan}\nІнтервал: {user['interval']} хв\nПоріг: {user['threshold']}%\nБіржа: {user['exchange']}\nPRO до: {expires_str}"
    await query.edit_message_text(text, reply_markup=main_menu(lang, plan))

async def get_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if get_plan(user_id) == "PRO":
        await query.edit_message_text("У вас вже є PRO!")
        return
    invoice_link = f"https://t.me/CryptoBot?start=pay_{PRO_PRICE_USDT}usdt_{user_id}_pro"
    keyboard = [[InlineKeyboardButton(f"Оплатити {PRO_PRICE_USDT} USDT", url=invoice_link)]]
    await query.edit_message_text("PRO-тариф — 50 USDT/міс\nОплата через @CryptoBot", reply_markup=InlineKeyboardMarkup(keyboard))

def get_all_funding():
    functions = [
        get_funding_bybit, get_funding_binance, get_funding_bitget, get_funding_mexc,
        get_funding_okx, get_funding_kucoin, get_funding_htx, get_funding_gateio, get_funding_bingx
    ]
    result = []
    for func in functions:
        try:
            result.extend(func())
        except Exception as e:
            print(f"{func.__name__} error:", e)
    return result

def format_funding_message(funding_list, plan, lang):
    funding_list.sort(key=lambda x: x["funding_rate"], reverse=True)
    lines = []
    for f in funding_list[:10]:
        rate = f["funding_rate"]
        time_str = f["next_funding_time"].strftime("%H:%M")
        symbol = f["symbol"]
        exchange = f["exchange"]
        if plan == "FREE" and rate > FREE_THRESHOLD:
            line = f"{rate:.2f}% о {time_str} на {exchange}"
        else:
            line = f"{rate:.2f}% о {time_str} → {symbol} ({exchange})"
        lines.append(line)
    return "\n".join(lines) if lines else get_text(lang, 'no_funding')

async def send_periodic_funding(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data
    user = get_user(user_id)
    if not user:
        return
    lang = user['language']
    plan = get_plan(user_id)
    try:
        funding_list = get_all_funding()
        filtered = [f for f in funding_list if f["funding_rate"] >= user['threshold']]
        if user['exchange'] != "ALL":
            filtered = [f for f in filtered if f["exchange"] == user['exchange']]
        message = format_funding_message(filtered, plan, lang)
        if message.strip():
            await context.bot.send_message(chat_id=user_id, text=get_text(lang, 'auto_message') + "\n" + message)
    except Exception as e:
        print("Periodic error:", e)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(lang_handler, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))
    application.add_handler(CallbackQueryHandler(account, pattern='^account$'))
    application.add_handler(CallbackQueryHandler(get_pro, pattern='^get_pro$'))

    application.run_polling()

if __name__ == '__main__':
    import asyncio

    asyncio.run(main())


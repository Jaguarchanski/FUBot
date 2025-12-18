# main.py — v13.15 (стабільна, працює на Render з Python 3.13)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
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

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        keyboard = [
            [InlineKeyboardButton("Українська", callback_data='lang_uk')],
            [InlineKeyboardButton("English", callback_data='lang_en')],
        ]
        update.message.reply_text(get_text('uk', 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))
        return
    lang = user['language']
    plan = get_plan(user_id)
    if plan == "FREE" and get_early_bird_count() < EARLY_BIRD_LIMIT:
        expires = datetime.now() + timedelta(days=PRO_DAYS)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        update.message.reply_text(get_text(lang, 'early_bird').format(num=count), reply_markup=main_menu(lang, "PRO"))
    else:
        update.message.reply_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))
    add_periodic_job(context, user_id)

def lang_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    lang = query.data.split('_')[1]
    user_id = query.from_user.id
    data = {"language": lang, "plan": "FREE", "interval": 5, "threshold": 1.5, "exchange": "Bybit", "timezone": "UTC"}
    add_or_update_user(user_id, data)
    query.edit_message_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, "FREE"))
    add_periodic_job(context, user_id)

def get_all_funding():
    functions = [
        get_funding_bybit, get_funding_binance, get_funding_bitget, get_funding_mexc,
        get_funding_okx, get_funding_kucoin, get_funding_htx, get_funding_gateio, get_funding_bingx
    ]
    result = []
    def run_func(func):
        try:
            result.extend(func())
        except Exception as e:
            print(f"{func.__name__} error:", e)
    threads = []
    for func in functions:
        t = threading.Thread(target=run_func, args=(func,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
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

def send_periodic_funding(context: CallbackContext):
    job = context.job
    user_id = job.context['user_id']
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
            def send():
                try:
                    context.bot.send_message(chat_id=user_id, text=get_text(lang, 'auto_message') + "\n" + message)
                except Exception as e:
                    print("Send error:", e)
            threading.Thread(target=send).start()
    except Exception as e:
        print("Periodic error:", e)

def add_periodic_job(context: CallbackContext, user_id: int):
    user = get_user(user_id)
    if not user:
        return
    current = context.job_queue.get_jobs_by_name(str(user_id))
    for j in current:
        j.schedule_removal()
    context.job_queue.run_repeating(
        send_periodic_funding,
        interval=user['interval'] * 60,
        first=10,
        context={"user_id": user_id},
        name=str(user_id)
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    data = query.data

    if data == 'top_funding':
        funding_list = get_all_funding()
        message = format_funding_message(funding_list, plan, lang)
        query.edit_message_text(get_text(lang, 'auto_message') + "\n" + message, reply_markup=main_menu(lang, plan))
    elif data == 'account':
        expires = user['plan_expires']
        expires_str = expires.strftime("%d.%m.%Y") if expires else "FREE"
        text = f"Тариф: {plan}\nІнтервал: {user['interval']} хв\nПоріг: {user['threshold']}%\nБіржа: {user['exchange']}\nPRO до: {expires_str}"
        query.edit_message_text(text, reply_markup=main_menu(lang, plan))
    elif data == 'get_pro':
        invoice_link = f"https://t.me/CryptoBot?start=pay_{PRO_PRICE_USDT}usdt_{user_id}_pro"
        keyboard = [[InlineKeyboardButton(f"Оплатити {PRO_PRICE_USDT} USDT", url=invoice_link)]]
        query.edit_message_text("PRO-тариф — 50 USDT/міс\nОплата через @CryptoBot", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(lang_handler, pattern='^lang_'))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    print("FundingBot 3.0 — ЗАПУЩЕНО!")
    updater.idle()

if __name__ == '__main__':
    main()

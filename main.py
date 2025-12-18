# main.py — v20.8 (працює на Render з Python 3.13, кнопки миттєво)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text
from config import BOT_TOKEN, USDT_WALLET, ADMIN_ID, EARLY_BIRD_LIMIT, PRO_PRICE_USDT, PRO_DAYS
from datetime import datetime, timedelta
import pytz
import nest_asyncio

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

FREE_THRESHOLD = 1.5
ALL_EXCHANGES = ['Bybit', 'Binance', 'Bitget', 'MEXC', 'OKX', 'KuCoin', 'HTX', 'Gate.io', 'BingX']
TIMEZONES = ['UTC', 'Europe/Kiev', 'Europe/London', 'America/New_York', 'America/Chicago', 'Asia/Dubai', 'Asia/Singapore', 'Asia/Hong_Kong']

# Стани для фільтра
EXCHANGE, THRESHOLD, INTERVAL, TIMEZONE = range(4)

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

async def filter_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']
    plan = get_plan(query.from_user.id)
    keyboard = []
    if plan == "PRO":
        for ex in ALL_EXCHANGES:
            keyboard.append([InlineKeyboardButton(ex, callback_data=f'ex_{ex}')])
    else:
        keyboard.append([InlineKeyboardButton("Bybit (FREE)", callback_data='ex_Bybit')])
    keyboard.append([InlineKeyboardButton(get_text(lang, 'back_button'), callback_data='back_to_menu')])
    await query.edit_message_text(get_text(lang, 'choose_exchange'), reply_markup=InlineKeyboardMarkup(keyboard))
    return EXCHANGE

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    lang = user['language']
    plan = get_plan(query.from_user.id)
    await query.edit_message_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))
    return ConversationHandler.END

# (додай інші стани фільтра з попереднього повідомлення)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Хендлери
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(lang_handler, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))
    application.add_handler(CallbackQueryHandler(account, pattern='^account$'))
    application.add_handler(CallbackQueryHandler(get_pro, pattern='^get_pro$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(filter_main, pattern='^filter_main$')],
        states={
            EXCHANGE: [CallbackQueryHandler(ex_handler, pattern='^ex_')],
            THRESHOLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, threshold_handler)],
            INTERVAL: [CallbackQueryHandler(interval_handler, pattern='^int_')],
            TIMEZONE: [CallbackQueryHandler(timezone_handler, pattern='^tz_')],
        },
        fallbacks=[CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$')],
    )
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

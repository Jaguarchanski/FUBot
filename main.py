# main.py — webhook для Render
import os
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text
from config import BOT_TOKEN
from datetime import datetime, timedelta

app = Flask(__name__)

# Telegram bot
application = Application.builder().token(BOT_TOKEN).build()

# Ініціалізація бази
init_db()

FREE_THRESHOLD = 1.5

# --- Меню ---
def main_menu(lang, plan):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'filter_button'), callback_data='filter_main')],
        [InlineKeyboardButton(get_text(lang, 'top_funding_button'), callback_data='top_funding')],
        [InlineKeyboardButton(get_text(lang, 'account_button'), callback_data='account')],
    ]
    if plan == 'FREE':
        keyboard.append([InlineKeyboardButton(get_text(lang, 'get_pro_button'), callback_data='get_pro')])
    return InlineKeyboardMarkup(keyboard)

# --- Команди ---
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

    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        await update.message.reply_text(get_text(lang, 'early_bird').format(num=count), reply_markup=main_menu(lang, "PRO"))
    else:
        await update.message.reply_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

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
    invoice_link = f"https://t.me/CryptoBot?start=pay_50usdt_{user_id}_pro"
    keyboard = [[InlineKeyboardButton("Оплатити 50 USDT", url=invoice_link)]]
    await query.edit_message_text("PRO-тариф — 50 USDT/міс\nОплата через @CryptoBot", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Фандінг ---
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

# --- Хендлери ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))
application.add_handler(CallbackQueryHandler(account, pattern='^account$'))
application.add_handler(CallbackQueryHandler(get_pro, pattern='^get_pro$'))

# --- Webhook ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string, application.bot)
        application.create_task(application.process_update(update))
        return 'ok', 200
    abort(403)

@app.route('/')
def index():
    return "Bot is alive!"

# --- Запуск ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

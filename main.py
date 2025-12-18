# main.py — v20.8 webhook (робочий на Render, без polling помилок)
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler
from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text
from config import BOT_TOKEN
from datetime import datetime, timedelta

app = Flask(__name__)

application = Application.builder().token(BOT_TOKEN).build()

init_db()

FREE_THRESHOLD = 1.5

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

    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        await update.message.reply_text(get_text(lang, 'early_bird').format(num=count), reply_markup=main_menu(lang, "PRO"))
    else:
        await update.message.reply_text(get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))

    context.job_queue.run_repeating(send_periodic_funding, interval=user['interval'] * 60, first=10, data=user_id, name=str(user_id))

# (додай інші хендлери: lang_handler, top_funding, account, get_pro, filter_main, back_to_menu тощо — з попереднього коду)

application.add_handler(CommandHandler("start", start))
# інші хендлери

@app.route('/' + BOT_TOKEN, methods=['POST'])
async def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string, application.bot)
        await application.process_update(update)
        return ''
    else:
        abort(403)

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    app.run()

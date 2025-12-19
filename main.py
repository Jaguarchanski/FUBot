import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from database import init_db, get_user, add_or_update_user, get_plan, increment_early_bird, get_early_bird_count
from funding_sources import *
from funding_sources_extra import *
from i18n import get_text

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://fubot.onrender.com/webhook

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN або WEBHOOK_URL не встановлені")

# =========================
# APP
# =========================
bot_app = Application.builder().token(BOT_TOKEN).build()
api = FastAPI()
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
    """Захист від BadRequest при незмінному тексті або кнопках"""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        if "Message is not modified" not in str(e):
            raise e


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


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        keyboard = [
            [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        ]
        await update.message.reply_text(
            "Вітаю! Оберіть мову / Choose language:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    lang = user['language']
    plan = get_plan(user_id)

    if plan == "FREE" and get_early_bird_count() < 500:
        expires = datetime.now() + timedelta(days=30)
        add_or_update_user(user_id, {"plan": "PRO", "plan_expires": expires})
        increment_early_bird()
        count = get_early_bird_count()
        await update.message.reply_text(
            get_text(lang, 'early_bird').format(num=count),
            reply_markup=main_menu(lang, "PRO")
        )
    else:
        await update.message.reply_text(
            get_text(lang, 'start_message'),
            reply_markup=main_menu(lang, plan)
        )


async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "lang_uk":
        add_or_update_user(user_id, {"language": "uk"})
        text = "✅ Мову встановлено: Українська"
    else:
        add_or_update_user(user_id, {"language": "en"})
        text = "✅ Language set: English"

    await safe_edit_message(query, text)
    # Після вибору мови відправляємо стартове меню
    plan = get_plan(user_id)
    lang = get_user(user_id)['language']
    await safe_edit_message(query, get_text(lang, 'start_message'), reply_markup=main_menu(lang, plan))


async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    funding_list = get_all_funding()
    message = format_funding_message(funding_list, plan, lang)
    await safe_edit_message(query, get_text(lang, 'auto_message') + "\n" + message, reply_markup=main_menu(lang, plan))


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
    await safe_edit_message(query, text, reply_markup=main_menu(lang, plan))


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


# =========================
# REGISTER HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(language_handler, pattern="^lang_"))
bot_app.add_handler(CallbackQueryHandler(top_funding, pattern='^top_funding$'))
bot_app.add_handler(CallbackQueryHandler(account, pattern='^account$'))
bot_app.add_handler(CallbackQueryHandler(get_pro, pattern='^get_pro$'))


# =========================
# FASTAPI
# =========================
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
    uvicorn.run("main:api", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

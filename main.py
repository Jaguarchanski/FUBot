# main.py — частина callback-ів
from telegram.error import BadRequest

async def safe_edit_message(query, text, reply_markup=None):
    """
    Безпечне оновлення повідомлення: перевіряє чи змінився текст або кнопки.
    """
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Ігноруємо помилку, якщо нічого не змінилось
            return
        raise

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
        f"Інтервал: {user['interval']} хв\n"
        f"Поріг: {user['threshold']}%\n"
        f"Біржа: {user['exchange']}\n"
        f"PRO до: {expires_str}"
    )
    await safe_edit_message(query, text, reply_markup=main_menu(lang, plan))


async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    lang = user['language']
    plan = get_plan(user_id)
    try:
        funding_list = get_all_funding()
        if not funding_list:
            message = get_text(lang, 'no_funding')
        else:
            message = format_funding_message(funding_list, plan, lang)
    except Exception as e:
        print("Funding fetch error:", e)
        message = get_text(lang, 'no_funding')

    await safe_edit_message(query, get_text(lang, 'auto_message') + "\n" + message, reply_markup=main_menu(lang, plan))


async def get_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if get_plan(user_id) == "PRO":
        await safe_edit_message(query, "У вас вже є PRO!")
        return
    invoice_link = f"https://t.me/CryptoBot?start=pay_50usdt_{user_id}_pro"
    keyboard = [[InlineKeyboardButton("Оплатити 50 USDT", url=invoice_link)]]
    await safe_edit_message(
        query,
        "PRO-тариф — 50 USDT/міс\nОплата через @CryptoBot",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def get_all_funding():
    functions = [
        get_funding_bybit, get_funding_binance, get_funding_bitget, get_funding_mexc,
        get_funding_okx, get_funding_kucoin, get_funding_htx, get_funding_gateio, get_funding_bingx
    ]
    result = []
    for func in functions:
        try:
            data = func()
            if data:
                result.extend(data)
        except Exception as e:
            print(f"{func.__name__} error:", e)
    return result

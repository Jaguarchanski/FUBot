import os
import aiosqlite
import datetime
import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

# Константи для станів ConversationHandler
WAITING_THRESHOLD, WAITING_UTC = 1, 2

# Список усіх бірж за ТЗ
ALL_EXCHANGES = ["Binance", "Bybit", "OKX", "Gateio", "Bitget", "BingX", "Kucoin", "MEXC", "HTX"]

def parse_date(date_str):
    if not date_str or date_str == "None": return None
    try:
        return datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return None

async def create_invoice(amount_usd):
    """Створення інвойсу через Crypto Pay API (CryptoBot)"""
    token = os.getenv("CRYPTO_BOT_TOKEN")
    if not token:
        return None
    
    url = "https://pay.cryptobots.run/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": token}
    payload = {
        "asset": "USDT",
        "amount": str(amount_usd),
        "description": "FUBot Premium Subscription - 1 Month",
        "paid_btn_name": "openBot",
        "paid_btn_url": "https://t.me/your_bot_username" # Замініть на ваш юзернейм
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            return data.get('result')
        except Exception as e:
            print(f"Invoice error: {e}")
            return None

async def get_settings_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("Top Fundings 📊", callback_data="show_top")],
        [InlineKeyboardButton("Exchanges Filter (9) 🏛", callback_data="manage_exchanges")],
        [InlineKeyboardButton("Set Threshold (%) 📉", callback_data="set_threshold")],
        [InlineKeyboardButton("Timezone (UTC) 🕒", callback_data="set_tz_manual")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile"), 
         InlineKeyboardButton("Premium 💎", callback_data="buy_premium")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "main_menu":
        await query.edit_message_text(
            "⚙️ **Головне меню та налаштування:**",
            reply_markup=await get_settings_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif query.data == "manage_exchanges":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
                plan = row[0] if row else "Free"
        
        status_text = "🏛 **Доступні біржі:**\n\n"
        for ex in ALL_EXCHANGES:
            status_text += f"✅ {ex}\n"
        
        if plan == "Free":
            status_text += "\n⚠️ *У Free версії дані відображаються лише для Bybit. Придбайте Premium для розблокування всіх 9 бірж.*"
        
        await query.edit_message_text(
            status_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, expiry_date, threshold, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
        
        if row:
            plan, expiry, thr, utc = row
            exp_str = f"\nДіє до: `{expiry[:10]}`" if expiry else ""
            text = (
                f"👤 **Мій профіль**\n\n"
                f"План: **{plan}**{exp_str}\n"
                f"Поріг алерту: `{thr}%`\n"
                f"Часовий пояс: `UTC {utc:+}`"
            )
        else:
            text = "Помилка завантаження профілю."

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    elif query.data == "buy_premium":
        text = (
            "💎 **Premium статус**\n\n"
            "• Доступ до 9 бірж (Binance, Bybit, OKX...)\n"
            "• Миттєві сповіщення (Alerts)\n"
            "• Перегляд прихованих монет з високим фандингом\n\n"
            "Вартість: **50 USDT / місяць**"
        )
        kb = [
            [InlineKeyboardButton("Оплатити через CryptoBot 💳", callback_data="pay_50_usdt")],
            [InlineKeyboardButton("« Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif query.data == "pay_50_usdt":
        invoice = await create_invoice(50)
        if invoice:
            kb = [
                [InlineKeyboardButton("Перейти до оплати 💸", url=invoice['pay_url'])],
                [InlineKeyboardButton("« Назад", callback_data="main_menu")]
            ]
            await query.edit_message_text(
                f"✅ **Рахунок створено!**\n\nСума: 50 USDT\nПісля оплати статус оновиться протягом хвилини.",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Помилка платіжної системи. Спробуйте пізніше або зверніться до адміна.")

    elif query.data == "show_top":
        await show_top_fundings(query, user_id)

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            plan, user_utc = row if row else ("Free", 0.0)
        
        async with db.execute("SELECT exchange, symbol, rate, next_funding_time FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = f"📊 **Top Fundings ({plan})**\n`Ex | Symbol  | Rate   | Time`\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    if not rows:
        text += "Дані ще завантажуються..."
    else:
        for ex, sym, rate, n_time in rows:
            # Логіка приховування за планом
            is_restricted = (plan == "Free" and ex.lower() != "bybit")
            display_sym = "HIDDEN" if is_restricted else sym[:7]
            
            dt = parse_date(n_time)
            time_str = (dt + datetime.timedelta(hours=user_utc)).strftime("%H:%M") if dt else "--:--"
            
            text += f"`{ex[:2].upper()} | {display_sym:<7} | {rate:+.3f}% | {time_str}`\n"
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="main_menu")]]), 
        parse_mode="Markdown"
    )

# Conversation states logic
async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🔢 Введіть новий поріг % (наприклад: 1.5):")
    return WAITING_THRESHOLD

async def start_utc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🕒 Введіть ваш UTC зсув (наприклад: 2 або -5):")
    return WAITING_UTC

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace(',', '.'))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Поріг збережено: {val}%", reply_markup=await get_settings_keyboard(update.effective_user.id))
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Помилка. Введіть число (наприклад 1.2)")
        return WAITING_THRESHOLD

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace('+', ''))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Час оновлено: UTC {val:+}", reply_markup=await get_settings_keyboard(update.effective_user.id))
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Помилка. Введіть число (наприклад 2)")
        return WAITING_UTC

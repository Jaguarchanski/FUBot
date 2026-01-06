import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import get_db
from services.funding_service import get_top_funding_rates

logger = logging.getLogger(__name__)

def get_main_keyboard():
    """Створює головне меню кнопок"""
    keyboard = [
        [
            InlineKeyboardButton("Binance", callback_data="ex_binance"),
            InlineKeyboardButton("Bybit", callback_data="ex_bybit")
        ],
        [
            InlineKeyboardButton("OKX", callback_data="ex_okx"),
            InlineKeyboardButton("Gate.io", callback_data="ex_gateio")
        ],
        [InlineKeyboardButton("📊 Мій профіль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Trader"
    
    try:
        db = await get_db()
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            plan = row[0] if row else "free"
        await db.close()

        welcome_text = (
            f"Привіт, {username}! 👋\n\n"
            f"Твій статус: **{plan.upper()}**\n\n"
            "Обери біржу, щоб побачити найвищі ставки фінансування:"
        )

        await update.message.reply_text(
            welcome_text, 
            reply_markup=get_main_keyboard(), 
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # Обов'язково відповідаємо на запит, щоб прибрати "годинник" на кнопці
    await query.answer()
    
    if data.startswith("ex_"):
        exchange_id = data.replace("ex_", "")
        await query.edit_message_text(text=f"⏳ Отримую дані з {exchange_id.capitalize()}... Зачекайте.")
        
        # Отримуємо звіт з CCXT
        report = await get_top_funding_rates(exchange_id)
        
        # Додаємо кнопку повернення
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]])
        
        await query.edit_message_text(
            text=report, 
            reply_markup=back_keyboard, 
            parse_mode="Markdown"
        )

    elif data == "back_to_main":
        await query.edit_message_text(
            text="Обери біржу для моніторингу:",
            reply_markup=get_main_keyboard()
        )
        
    elif data == "profile":
        user_id = update.effective_user.id
        profile_text = f"👤 **Твій профіль**\n\nID: `{user_id}`\nСтатус: `Free`\n\nМожливість налаштування сповіщень буде доступна незабаром!"
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]])
        await query.edit_message_text(text=profile_text, reply_markup=back_keyboard, parse_mode="Markdown")

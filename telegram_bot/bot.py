import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import get_db

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    try:
        db = await get_db()
        # Реєструємо користувача (якщо вже є — нічого не робимо)
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        
        # Отримуємо дані користувача
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            plan = row[0] if row else "free"
        await db.close()

        # Створюємо меню вибору бірж
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
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            f"Привіт, {username}! 👋\n\n"
            f"Твій статус: **{plan.upper()}**\n"
            "Я допоможу тобі моніторити ставки фінансування (Funding Rates).\n\n"
            "Оберіть біржу для перегляду актуальних ставок:"
        )

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Помилка в start_command: {e}")
        await update.message.reply_text("Вибачте, сталася помилка при ініціалізації профілю.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("ex_"):
        exchange_name = data.replace("ex_", "").capitalize()
        await query.edit_message_text(
            text=f"Ви обрали {exchange_name}. Зараз я завантажую актуальні дані з API... ⏳"
        )
        # Тут пізніше додамо виклик функції з ccxt
    elif data == "profile":
        await query.edit_message_text(text="Це твій профіль. Тут буде список твоїх підписок.")
